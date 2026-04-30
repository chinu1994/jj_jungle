from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SimpleJungle(models.Model):
    _name = 'simple.jungle'
    _description = 'Simple Jungle Model'
    _rec_name = 'name'

    # Basic fields
    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    active = fields.Boolean(string='Active', default=True)

    # Status field with selection
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ], string='Status', default='draft', required=True, readonly=True)

    # Many2one fields - with domain for filtering
    company_id = fields.Many2one('res.company', string='Company')
    user_id = fields.Many2one('res.users', string='Responsible User',
                              domain="[('company_id', '=', company_id)]")

    # Make name and email readonly when state is confirm
    @api.depends('state')
    def _compute_readonly(self):
        for record in self:
            if record.state == 'confirm':
                record.name_readonly = True
                record.email_readonly = True
            else:
                record.name_readonly = False
                record.email_readonly = False

    # Onchange to clear user when company changes
    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.user_id = False
            return {
                'domain': {
                    'user_id': [('company_id', '=', self.company_id.id)]
                }
            }
        else:
            return {
                'domain': {
                    'user_id': []
                }
            }

    # Email validation
    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email and '@' not in record.email:
                raise ValidationError("Invalid email format! Email must contain '@'")

    # Confirm action - creates company and user from name and email BOTH
    def action_confirm(self):
        for record in self:
            if record.state == 'draft':
                # 1. Create or Update Company
                if not record.company_id:
                    company_vals = {
                        'name': f"{record.name} - {record.email.split('@')[0]}",
                        'email': record.email,
                    }
                    company = self.env['res.company'].create(company_vals)
                    record.company_id = company.id
                else:
                    # Update existing company name
                    record.company_id.write({
                        'name': f"{record.name} - {record.email.split('@')[0]}",
                        'email': record.email,
                    })

                # 2. Create or Update User
                existing_user = self.env['res.users'].search([('login', '=', record.email)], limit=1)
                if existing_user:
                    # Update existing user
                    existing_user.write({
                        'name': f"{record.name} ({record.email})",
                    })
                    record.user_id = existing_user.id
                else:
                    # Create new user
                    user_vals = {
                        'name': f"{record.name}",
                        'login': record.email,
                        'email': record.email,
                        'company_id': record.company_id.id,
                        'company_ids': [(6, 0, [record.company_id.id])],
                    }
                    user = self.env['res.users'].create(user_vals)
                    record.user_id = user.id

                record.state = 'confirm'

    # Draft action - reset to draft
    def action_draft(self):
        for record in self:
            record.state = 'draft'
            record.company_id = False
            record.user_id = False