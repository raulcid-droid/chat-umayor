from odoo import http
from odoo.http import request


class MiModuloController(http.Controller):

    @http.route('/mi_modulo/ejemplo', type='http', auth='user')
    def index(self, **kwargs):
        return request.render('mi_modulo.template_ejemplo', {})
