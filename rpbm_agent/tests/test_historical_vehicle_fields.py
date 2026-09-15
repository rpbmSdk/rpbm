from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError

from .. import hooks
from ..controllers import main


HISTORICAL_FIELDS = {
    'x_studio_field_NVioD',
    'x_studio_field_KyCjB',
    'x_studio_field_ZhaeY',
    'x_studio_field_PfJlB',
    'x_studio_field_TAhpP',
    'x_studio_field_i8fWl',
    'x_studio_field_Eh6Wd',
    'x_studio_immatriculation_',
    'x_studio_many2one_field_rP62C',
    'x_studio_many2one_field_DkgHx',
    'x_studio_vin_',
    'x_studio_nergie_moteur',
    'x_studio_dtails_modle',
    'x_studio_date_1re_mec',
}


class _Record:
    def __init__(self, record_id, **values):
        self.id = record_id
        self._values = values
        self.write_calls = []

    def read(self, field_names):
        return [{field_name: self._values.get(field_name) for field_name in field_names}]

    def write(self, values):
        self.write_calls.append(values)
        self._values.update(values)
        return True


class _RecordSet(list):
    def read(self, field_names):
        return self[0].read(field_names) if self else []

    def write(self, values):
        for record in self:
            record.write(values)
        return True


class _AccessDeniedRecord(_Record):
    def read(self, field_names):
        raise AccessError('read forbidden')


class _WriteDeniedRecord(_Record):
    def write(self, values):
        raise AccessError('write forbidden')


class _Model:
    def __init__(
        self,
        name,
        records=(),
        field_names=(),
        allow_create=True,
        deny_search=False,
        deny_read=False,
        deny_write=False,
    ):
        self._name = name
        self._records = list(records)
        self._fields = {field_name: object() for field_name in field_names}
        self.allow_create = allow_create
        self.deny_search = deny_search
        self.deny_read = deny_read
        self.deny_write = deny_write
        self.create_calls = []

    def with_context(self, **kwargs):
        return self

    def search(self, domain, limit=None):
        if self.deny_search:
            raise AccessError('search forbidden')
        records = self._records
        for field_name, operator, expected in domain:
            if field_name == 'id' and operator == '=':
                records = [record for record in records if record.id == expected]
            elif field_name == 'x_name' and operator == '!=':
                records = [record for record in records if record._values.get('x_name')]
        if limit:
            records = records[:limit]
        if self.deny_write:
            records = [
                _WriteDeniedRecord(record.id, **record._values)
                for record in records
            ]
        return _RecordSet(records)

    def browse(self, record_id):
        records = [record for record in self._records if record.id == record_id]
        if self.deny_read:
            records = [_AccessDeniedRecord(record.id, **record._values) for record in records]
        elif self.deny_write:
            records = [_WriteDeniedRecord(record.id, **record._values) for record in records]
        return _RecordSet(records)

    def create(self, values):
        if not self.allow_create:
            raise AccessError('create forbidden')
        self.create_calls.append(values)
        record = _Record(len(self._records) + 100, **values)
        self._records.append(record)
        return record


class _Environment(dict):
    pass


def _environment(
    *,
    vehicle_values=None,
    model_values=None,
    brand_values=None,
    historical_brands=(),
    historical_models=(),
    allow_reference_creation=True,
):
    vehicle_model = _Model(
        'fleet.vehicle.model',
        [_Record(11, **(model_values or {'name': 'Clio', 'brand_id': [21, 'Renault']}))],
    )
    brand_model = _Model(
        'fleet.vehicle.model.brand',
        [_Record(21, **(brand_values or {'name': 'Renault'}))],
    )
    fleet_model = _Model(
        'fleet.vehicle',
        [_Record(
            7,
            **(
                vehicle_values
                or {
                    'license_plate': 'AB-123-CD',
                    'vin_sn': 'VIN123',
                    'model_id': [11, 'Clio'],
                    'x_studio_detail_model': 'Clio IV',
                    'x_studio_date_mec': '2020-09-15',
                    'fuel_type': 'diesel',
                }
            ),
        )],
    )
    target_fields = set(main.HISTORICAL_VEHICLE_FIELD_TARGETS['crm.lead'].values())
    target_fields.update(main.HISTORICAL_VEHICLE_FIELD_TARGETS['sale.order'].values())
    return _Environment(
        {
            'fleet.vehicle': fleet_model,
            'fleet.vehicle.model': vehicle_model,
            'fleet.vehicle.model.brand': brand_model,
            'x_rpbm_marques_voitures': _Model(
                'x_rpbm_marques_voitures',
                historical_brands,
                field_names=('x_name',),
                allow_create=allow_reference_creation,
            ),
            'x_rpbm_modeles_voitures': _Model(
                'x_rpbm_modeles_voitures',
                historical_models,
                field_names=('x_name',),
                allow_create=allow_reference_creation,
            ),
            'crm.lead': _Model('crm.lead', field_names=target_fields),
            'sale.order': _Model('sale.order', field_names=target_fields),
        }
    )


class TestHistoricalVehicleFields(TestCase):
    def test_route_rejects_unknown_model_and_invalid_vehicle_id(self):
        env = _environment()

        with self.assertRaises(UserError):
            main._historical_vehicle_payload(env, 7, 'res.partner')
        with self.assertRaises(UserError):
            main._historical_vehicle_payload(env, 0, 'crm.lead')
        with self.assertRaises(UserError):
            main._historical_vehicle_payload(env, True, 'crm.lead')

    def test_fleet_alias_specs_are_absent_and_required_specs_remain(self):
        specs = {(spec['model'], spec['name']) for spec in hooks.FIELDS_TO_ENSURE}
        aliases = {
            (model, field_name)
            for model in ('crm.lead', 'sale.order')
            for field_name in (
                'x_rpbm_vehicle_brand_id',
                'x_rpbm_vehicle_model_id',
                'x_rpbm_vehicle_brand_name',
                'x_rpbm_vehicle_model_name',
                'x_rpbm_vehicle_vin',
                'x_rpbm_vehicle_detail_model',
                'x_rpbm_vehicle_fuel_type',
                'x_rpbm_vehicle_date_mec',
            )
        }
        self.assertFalse(aliases & specs)
        self.assertIn(('crm.lead', 'x_studio_vehicle_id'), specs)
        self.assertIn(('sale.order', 'x_studio_vehicle_id'), specs)
        self.assertIn(('crm.lead', 'x_studio_categorie_xglass'), specs)
        self.assertIn(('sale.order', 'x_studio_categorie_xglass'), specs)
        self.assertIn(('sale.order', 'x_rpbm_vsf_constructor_reference'), specs)
        self.assertNotIn('x_studio_field_aIM13', HISTORICAL_FIELDS)

    def test_legacy_migration_symbol_is_a_noop(self):
        class ExplodingEnvironment:
            @property
            def registry(self):
                raise AssertionError('the compatibility migration must not inspect the environment')

        self.assertIsNone(hooks._replace_legacy_vehicle_references(ExplodingEnvironment()))

    def test_route_returns_explicit_crm_payload_and_reuses_normalized_references(self):
        env = _environment(
            historical_brands=[_Record(31, x_name='Renault')],
            historical_models=[_Record(41, x_name='Clio')],
            vehicle_values={
                'license_plate': ' AB-123-CD ',
                'vin_sn': ' VIN123 ',
                'model_id': [11, 'Clio'],
                'x_studio_detail_model': ' Clio IV ',
                'x_studio_date_mec': '2020-09-15',
                'fuel_type': 'diesel',
                'x_studio_field_aIM13': 123456,
            },
            model_values={'name': ' cLiO ', 'brand_id': [21, 'Renault']},
            brand_values={'name': ' rEnAuLt '},
        )

        with patch.object(main, 'request', SimpleNamespace(env=env)):
            payload = main.AgentController().prepare_historical_vehicle_fields(7, 'crm.lead')

        self.assertEqual(payload['warnings'], [])
        self.assertEqual(
            payload['values'],
            {
                'x_studio_field_NVioD': 'AB-123-CD',
                'x_studio_field_PfJlB': 'VIN123',
                'x_studio_field_KyCjB': [31, 'Renault'],
                'x_studio_field_ZhaeY': [41, 'Clio'],
                'x_studio_field_TAhpP': 'Diesel',
                'x_studio_field_i8fWl': 'Clio IV',
                'x_studio_field_Eh6Wd': '09/2020',
            },
        )
        self.assertTrue(set(payload['values']) <= HISTORICAL_FIELDS)
        self.assertNotIn('x_studio_field_aIM13', payload['values'])

    def test_route_uses_sale_order_mirrors(self):
        env = _environment(
            historical_brands=[_Record(31, x_name='Renault')],
            historical_models=[_Record(41, x_name='Clio')],
        )
        payload = main._historical_vehicle_payload(env, 7, 'sale.order')

        self.assertEqual(payload['values']['x_studio_immatriculation_'], 'AB-123-CD')
        self.assertEqual(payload['values']['x_studio_many2one_field_rP62C'], [31, 'Renault'])
        self.assertEqual(payload['values']['x_studio_many2one_field_DkgHx'], [41, 'Clio'])
        self.assertEqual(payload['values']['x_studio_nergie_moteur'], 'Diesel')
        self.assertEqual(payload['values']['x_studio_date_1re_mec'], '09/2020')

    def test_reference_prefers_the_single_canonical_spelling(self):
        env = _environment(
            historical_brands=[_Record(31, x_name='PEUGEOT'), _Record(32, x_name='peugeot')],
            historical_models=[_Record(41, x_name='3008')],
            vehicle_values={
                'license_plate': 'AB-123-CD',
                'vin_sn': '',
                'model_id': [11, '3008'],
                'x_studio_detail_model': '',
                'x_studio_date_mec': False,
                'fuel_type': 'gasoline',
            },
            model_values={'name': '3008', 'brand_id': [21, 'PEUGEOT']},
            brand_values={'name': 'PEUGEOT'},
        )

        payload = main._historical_vehicle_payload(env, 7, 'crm.lead')

        self.assertEqual(payload['warnings'], [])
        self.assertEqual(payload['values']['x_studio_field_KyCjB'], [31, 'PEUGEOT'])
        self.assertEqual(payload['values']['x_studio_field_ZhaeY'], [41, '3008'])

    def test_missing_reference_names_warn_and_do_not_create_or_write(self):
        env = _environment(
            model_values={'name': '', 'brand_id': False},
            brand_values={'name': ''},
        )

        payload = main._historical_vehicle_payload(env, 7, 'crm.lead')

        self.assertNotIn('x_studio_field_KyCjB', payload['values'])
        self.assertNotIn('x_studio_field_ZhaeY', payload['values'])
        self.assertEqual(env['x_rpbm_marques_voitures'].create_calls, [])
        self.assertEqual(env['x_rpbm_modeles_voitures'].create_calls, [])
        self.assertTrue(any('Marque Fleet absent' in warning for warning in payload['warnings']))
        self.assertTrue(any('Modèle Fleet absent' in warning for warning in payload['warnings']))

    def test_ambiguous_references_warn_and_write_first_match(self):
        env = _environment(
            historical_brands=[_Record(31, x_name='RENAULT'), _Record(32, x_name='renault')],
            historical_models=[_Record(41, x_name='CLIO'), _Record(42, x_name='clio')],
        )

        payload = main._historical_vehicle_payload(env, 7, 'crm.lead')

        self.assertEqual(payload['values']['x_studio_field_KyCjB'], [31, 'RENAULT'])
        self.assertEqual(payload['values']['x_studio_field_ZhaeY'], [41, 'CLIO'])
        self.assertEqual(env['x_rpbm_marques_voitures'].create_calls, [])
        self.assertEqual(env['x_rpbm_modeles_voitures'].create_calls, [])
        self.assertTrue(any(
            'Marque historique ambigu' in warning and 'première correspondance retenue' in warning
            for warning in payload['warnings']
        ))
        self.assertTrue(any(
            'Modèle historique ambigu' in warning and 'première correspondance retenue' in warning
            for warning in payload['warnings']
        ))

    def test_metadata_fills_missing_vin_and_date_for_historical_payload(self):
        env = _environment(
            vehicle_values={
                'license_plate': 'AB-123-CD',
                'vin_sn': False,
                'model_id': False,
                'x_studio_detail_model': '',
                'x_studio_date_mec': False,
                'fuel_type': 'gasoline',
            }
        )

        payload = main._historical_vehicle_payload(
            env,
            7,
            'crm.lead',
            {'vin': ' VF123456789 ', 'dateMec': '09/2020'},
        )

        self.assertEqual(payload['values']['x_studio_field_PfJlB'], 'VF123456789')
        self.assertEqual(payload['values']['x_studio_field_Eh6Wd'], '09/2020')

    def test_fleet_enrichment_writes_only_missing_metadata(self):
        env = _environment(
            vehicle_values={
                'license_plate': 'AB-123-CD',
                'vin_sn': '',
                'model_id': False,
                'x_studio_detail_model': '',
                'x_studio_date_mec': False,
                'fuel_type': 'gasoline',
            }
        )
        vehicle = env['fleet.vehicle'].browse(7)[0]
        warnings = []

        written = main._enrich_fleet_vehicle_from_metadata(
            vehicle,
            {'vin': 'VIN-META', 'dateMec': '09/2020'},
            warnings,
        )

        self.assertEqual(warnings, [])
        self.assertEqual(written['vin_sn'], 'VIN-META')
        self.assertEqual(written['x_studio_date_mec'].strftime('%m/%Y'), '09/2020')
        self.assertEqual(vehicle._values['vin_sn'], 'VIN-META')
        self.assertEqual(vehicle._values['x_studio_date_mec'].strftime('%m/%Y'), '09/2020')

        vehicle._values['vin_sn'] = 'VIN-EXISTANT'
        vehicle._values['x_studio_date_mec'] = '2021-01-15'
        written = main._enrich_fleet_vehicle_from_metadata(
            vehicle,
            {'vin': 'VIN-NOUVEAU', 'dateMec': '02/2022'},
            warnings,
        )

        self.assertEqual(written, {})
        self.assertEqual(vehicle._values['vin_sn'], 'VIN-EXISTANT')
        self.assertEqual(vehicle._values['x_studio_date_mec'], '2021-01-15')

    def test_fleet_enrichment_repairs_legacy_malformed_vin(self):
        env = _environment(
            vehicle_values={
                'license_plate': 'AB-123-CD',
                'vin_sn': 'var  = VF3MRHNSMNS091999;',
                'model_id': False,
                'x_studio_detail_model': '',
                'x_studio_date_mec': False,
                'fuel_type': 'gasoline',
            }
        )
        vehicle = env['fleet.vehicle'].browse(7)[0]

        written = main._enrich_fleet_vehicle_from_metadata(
            vehicle,
            {'vin': ' VF3MRHNSMNS091999 '},
            [],
        )

        self.assertEqual(written, {'vin_sn': 'VF3MRHNSMNS091999'})
        self.assertEqual(vehicle._values['vin_sn'], 'VF3MRHNSMNS091999')

    def test_historical_payload_repairs_malformed_vin_when_fleet_write_is_denied(self):
        env = _environment(
            vehicle_values={
                'license_plate': 'AB-123-CD',
                'vin_sn': 'var  = VF3MRHNSMNS091999;',
                'model_id': False,
                'x_studio_detail_model': '',
                'x_studio_date_mec': False,
                'fuel_type': 'gasoline',
            }
        )
        env['fleet.vehicle'].deny_write = True
        vehicle = env['fleet.vehicle'].search([('id', '=', 7)], limit=1)[0]

        written = main._enrich_fleet_vehicle_from_metadata(
            vehicle,
            {'vin': ' VF3MRHNSMNS091999 '},
            [],
        )
        payload = main._historical_vehicle_payload(
            env,
            7,
            'crm.lead',
            {'vin': ' VF3MRHNSMNS091999 '},
        )

        self.assertEqual(written, {})
        self.assertEqual(payload['values']['x_studio_field_PfJlB'], 'VF3MRHNSMNS091999')

    def test_historical_payload_preserves_valid_vin(self):
        env = _environment(
            vehicle_values={
                'license_plate': 'AB-123-CD',
                'vin_sn': 'VF3MRHNSMNS091999',
                'model_id': False,
                'x_studio_detail_model': '',
                'x_studio_date_mec': False,
                'fuel_type': 'gasoline',
            }
        )
        vehicle = env['fleet.vehicle'].browse(7)[0]

        written = main._enrich_fleet_vehicle_from_metadata(
            vehicle,
            {'vin': 'VF1RFB00367123456'},
            [],
        )
        payload = main._historical_vehicle_payload(
            env,
            7,
            'crm.lead',
            {'vin': 'VF1RFB00367123456'},
        )

        self.assertEqual(written, {})
        self.assertEqual(vehicle._values['vin_sn'], 'VF3MRHNSMNS091999')
        self.assertEqual(payload['values']['x_studio_field_PfJlB'], 'VF3MRHNSMNS091999')

    def test_invalid_metadata_date_warns_without_writing(self):
        env = _environment()
        vehicle = env['fleet.vehicle'].browse(7)[0]
        warnings = []

        written = main._enrich_fleet_vehicle_from_metadata(
            vehicle,
            {'dateMec': 'date-invalide'},
            warnings,
        )

        self.assertEqual(written, {})
        self.assertTrue(any("Date MEC X'Glass invalide" in warning for warning in warnings))
        self.assertEqual(vehicle.write_calls, [])

    def test_fleet_enrichment_access_error_is_non_blocking(self):
        env = _environment(
            vehicle_values={
                'license_plate': 'AB-123-CD',
                'vin_sn': '',
                'model_id': False,
                'x_studio_detail_model': '',
                'x_studio_date_mec': False,
                'fuel_type': 'gasoline',
            }
        )
        env['fleet.vehicle'].deny_write = True
        vehicle = env['fleet.vehicle'].search([('id', '=', 7)], limit=1)[0]
        warnings = []

        written = main._enrich_fleet_vehicle_from_metadata(
            vehicle,
            {'vin': 'VIN-META'},
            warnings,
        )

        self.assertEqual(written, {})
        self.assertTrue(any('Écriture des métadonnées Fleet interdite' in warning for warning in warnings))

    def test_reference_creation_and_acl_warning(self):
        env = _environment()
        payload = main._historical_vehicle_payload(env, 7, 'crm.lead')

        self.assertEqual(payload['values']['x_studio_field_KyCjB'], [100, 'Renault'])
        self.assertEqual(payload['values']['x_studio_field_ZhaeY'], [100, 'Clio'])
        self.assertEqual(env['x_rpbm_marques_voitures'].create_calls, [{'x_name': 'Renault'}])
        self.assertEqual(env['x_rpbm_modeles_voitures'].create_calls, [{'x_name': 'Clio'}])

        restricted_env = _environment(allow_reference_creation=False)
        restricted_payload = main._historical_vehicle_payload(restricted_env, 7, 'crm.lead')
        self.assertNotIn('x_studio_field_KyCjB', restricted_payload['values'])
        self.assertNotIn('x_studio_field_ZhaeY', restricted_payload['values'])
        self.assertTrue(any('interdite par les droits' in warning for warning in restricted_payload['warnings']))

    def test_supported_energy_mappings_and_unknown_value(self):
        expected = {
            'diesel': 'Diesel',
            'gasoline': 'Essence',
            'electric': 'Électrique',
            'full_hybrid': 'Hybride',
            'plug_in_hybrid_diesel': 'Hybride',
        }
        for source, label in expected.items():
            with self.subTest(source=source):
                env = _environment(
                    vehicle_values={
                        'license_plate': 'AB-123-CD',
                        'vin_sn': '',
                        'model_id': False,
                        'x_studio_detail_model': '',
                        'x_studio_date_mec': False,
                        'fuel_type': source,
                    }
                )
                payload = main._historical_vehicle_payload(env, 7, 'crm.lead')
                self.assertEqual(payload['values']['x_studio_field_TAhpP'], label)

        env = _environment(
            vehicle_values={
                'license_plate': 'AB-123-CD',
                'vin_sn': '',
                'model_id': False,
                'x_studio_detail_model': '',
                'x_studio_date_mec': False,
                'fuel_type': 'hydrogen',
            }
        )
        payload = main._historical_vehicle_payload(env, 7, 'crm.lead')
        self.assertNotIn('x_studio_field_TAhpP', payload['values'])
        self.assertTrue(any('non prise en charge' in warning for warning in payload['warnings']))

    def test_inconnu_is_never_created(self):
        env = _environment(
            brand_values={'name': 'Inconnu'},
            model_values={'name': 'Inconnu', 'brand_id': [21, 'Inconnu']},
        )

        payload = main._historical_vehicle_payload(env, 7, 'crm.lead')

        self.assertNotIn('x_studio_field_KyCjB', payload['values'])
        self.assertNotIn('x_studio_field_ZhaeY', payload['values'])
        self.assertEqual(env['x_rpbm_marques_voitures'].create_calls, [])
        self.assertEqual(env['x_rpbm_modeles_voitures'].create_calls, [])

    def test_fleet_vehicle_search_access_error_is_a_warning(self):
        env = _environment()
        env['fleet.vehicle'].deny_search = True

        payload = main._historical_vehicle_payload(env, 7, 'crm.lead')

        self.assertEqual(payload['values'], {})
        self.assertTrue(any('Lecture du véhicule Fleet interdite' in warning for warning in payload['warnings']))

    def test_fleet_model_and_brand_read_access_errors_are_warnings(self):
        model_denied_env = _environment()
        model_denied_env['fleet.vehicle.model'].deny_read = True
        model_denied_payload = main._historical_vehicle_payload(model_denied_env, 7, 'crm.lead')
        self.assertNotIn('x_studio_field_KyCjB', model_denied_payload['values'])
        self.assertNotIn('x_studio_field_ZhaeY', model_denied_payload['values'])
        self.assertTrue(any('Lecture du modèle Fleet interdite' in warning for warning in model_denied_payload['warnings']))

        brand_denied_env = _environment()
        brand_denied_env['fleet.vehicle.model.brand'].deny_read = True
        brand_denied_payload = main._historical_vehicle_payload(brand_denied_env, 7, 'crm.lead')
        self.assertNotIn('x_studio_field_KyCjB', brand_denied_payload['values'])
        self.assertIn('x_studio_field_ZhaeY', brand_denied_payload['values'])
        self.assertTrue(any('Lecture de la marque Fleet interdite' in warning for warning in brand_denied_payload['warnings']))
