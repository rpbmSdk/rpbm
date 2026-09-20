from unittest import TestCase

from ..controllers.main import LABOR_PRODUCT_BY_RATE, _labor_operation_payload


class TestLaborOperations(TestCase):
    def _operation(self, **values):
        return {
            "id": 41,
            "temps": 1.25,
            "taux": "T1",
            "activite": {"code": "C1", "nature": "Carrosserie"},
            "operationTemps": {"id": 7, "libelle": "Dépose / pose"},
            **values,
        }

    def test_supported_rates_map_only_to_the_validated_hourly_services(self):
        self.assertEqual(LABOR_PRODUCT_BY_RATE, {"T1": 24, "T2": 23, "T3": 113})
        for rate, product_id in LABOR_PRODUCT_BY_RATE.items():
            payload = _labor_operation_payload(99, self._operation(taux=rate))
            self.assertEqual(payload["productId"], product_id)
            self.assertFalse(payload["unavailableReason"])
            self.assertEqual(payload["key"], "99:41")

    def test_activity_code_normalizes_carrosserie_and_mecanique_rates(self):
        payload = _labor_operation_payload(99, self._operation(taux=False, activite={"code": "M3"}))
        self.assertEqual(payload["rate"], "T3")
        self.assertEqual(payload["productId"], 113)

    def test_invalid_duration_unknown_rate_and_missing_identifier_cannot_be_added(self):
        self.assertTrue(_labor_operation_payload(99, self._operation(temps=0))["unavailableReason"])
        self.assertTrue(_labor_operation_payload(99, self._operation(taux="T9", activite={"code": "X9"}))["unavailableReason"])
        self.assertTrue(_labor_operation_payload(99, self._operation(id=False, operationTemps={}))["unavailableReason"])
