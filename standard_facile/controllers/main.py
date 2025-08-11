from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
import base64
import csv
import io

class StandardFacileController(http.Controller):
    @http.route('/standard_facile', type='http', auth='user', website=True)
    def standard_facile_form(self, **kwargs):
        user = request.env.user
        if not user.has_group('base.group_user'):
            raise AccessDenied()
        return request.render('standard_facile.upload_csv_template', {})

    @http.route('/standard_facile/upload', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def standard_facile_upload(self, uploaded_file=None, **kwargs):
        user = request.env.user
        if not user.has_group('base.group_user'):
            raise AccessDenied()
        errors = []
        success = False
        if uploaded_file:
            try:
                file_content = uploaded_file.read()
                file_stream = io.StringIO(file_content.decode('utf-8'))
                reader = csv.DictReader(file_stream)
                
                # Remplacer par la logique de création d'enregistrements
                StandardFacileModel = request.env['x_studio_standard_facile_call']
                csv_fields= {
                    'STATUT': 'x_studio_statut',
                    'APPEL ENTRANT': 'x_studio_appel_entrant',
                    'JOUR': 'x_studio_date',
                    'HEURE': 'x_studio_hour',
                    'REDIRECTION': 'x_studio_appel_redirection',
                    'DUR�E (en seconde)':'x_studio_appel_duree',
                    'ANNOTATION':'x_studio_appel_note'
                }
                for row in reader:
                    # Search for similar records based on fields x_studio_statut, x_studio_appel_entrant, x_studio_date, x_studio_hour
                    existing_record = StandardFacileModel.search([
                        ('x_studio_statut', '=', row.get('STATUT')),
                        ('x_studio_appel_entrant', '=', row.get('APPEL ENTRANT')),
                        ('x_studio_date', '=', row.get('JOUR')),
                        ('x_studio_hour', '=', row.get('HEURE')),
                    ], limit=1)
                    if existing_record:
                        # Update the existing record
                        existing_record.write({
                            'x_studio_statut': row.get('STATUT'),
                            'x_studio_appel_entrant': row.get('APPEL ENTRANT'),
                            'x_studio_date': row.get('JOUR'),
                            'x_studio_hour': row.get('HEURE'),
                            'x_studio_appel_redirection': row.get('REDIRECTION'),
                            'x_studio_appel_duree': row.get('DUR�E (en seconde)'),
                            'x_studio_appel_note': row.get('ANNOTATION')
                        })
                    else:
                        # Create a new record
                        StandardFacileModel.create({
                            'x_studio_statut': row.get('STATUT'),
                            'x_studio_appel_entrant': row.get('APPEL ENTRANT'),
                            'x_studio_date': row.get('JOUR'),
                            'x_studio_hour': row.get('HEURE'),
                            'x_studio_appel_redirection': row.get('REDIRECTION'),
                            'x_studio_appel_duree': row.get('DUR�E (en seconde)'),
                            'x_studio_appel_note': row.get('ANNOTATION')
                        })
                success = True
            except Exception as e:
                errors.append(str(e))
        else:
            errors.append("Aucun fichier n'a été envoyé.")
        if success:
            return request.render('standard_facile.success_template', {})
        else:
            return request.render('standard_facile.upload_csv_template', {'errors': errors})
