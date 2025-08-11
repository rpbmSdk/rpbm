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
                for row in reader:
                    # Exemple : request.env['votre.modele'].create(row)
                    pass
                success = True
            except Exception as e:
                errors.append(str(e))
        else:
            errors.append("Aucun fichier n'a été envoyé.")
        if success:
            return request.render('standard_facile.success_template', {})
        else:
            return request.render('standard_facile.upload_csv_template', {'errors': errors})
