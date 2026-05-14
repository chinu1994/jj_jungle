# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class JxSocialJobService(models.AbstractModel):
    _name = 'jx.social.job.service'
    _description = 'JX Social Job Queue & Publishing Service'

    # ===================================================================
    # 7.3 publish_queued_posts - Cron Handler
    # ===================================================================
    @api.model
    def publish_queued_posts(self):
        """
        Main cron job handler as per Section 7.3
        """
        _logger.info("JX Social: Starting publish_queued_posts cron")

        schedules = self.env['jx.social.schedule'].search([
            ('state', '=', 'queued'),
            ('scheduled_at', '<=', fields.Datetime.now())
        ], order='scheduled_at ASC', limit=50)

        if not schedules:
            return

        for schedule in schedules:
            try:
                schedule = schedule.with_context(no_recompute=True)

                # Set to publishing before API call
                schedule.write({'state': 'publishing'})
                self.env.cr.commit()

                # ==================== Get Connector ====================
                registry = self.env['jx.social.connector.registry']
                connector = registry.get_connector(schedule.social_account_id.provider)

                # Publish
                result = connector.publish_post(schedule)

                # On Success
                if result and result.get('external_post_id'):
                    schedule.write({
                        'state': 'sent',
                        'external_post_id': result.get('external_post_id'),
                        'published_at': result.get('published_at') or fields.Datetime.now(),
                        'provider_response': str(result.get('raw_response', {}))
                    })
                else:
                    raise Exception("No external_post_id returned")

            except Exception as e:
                error_msg = str(e)
                _logger.error("Failed to publish schedule %s: %s", schedule.id, error_msg)

                try:
                    schedule.write({
                        'state': 'failed',
                        'error_message': error_msg[:500],
                        'retry_count': schedule.retry_count + 1,
                    })
                except:
                    _logger.error("Failed to update failed status for schedule %s", schedule.id)

                # TODO: Add audit log here later
                self._log_publish_error(schedule, error_msg)

            finally:
                try:
                    self.env.cr.commit()
                except Exception as commit_error:
                    _logger.error("Commit failed for schedule %s: %s", schedule.id, commit_error)

        _logger.info("JX Social: Completed publish_queued_posts. Processed: %s", len(schedules))

    def _log_publish_error(self, schedule, error_msg):
        """Placeholder for audit logging"""
        try:
            self.env['jx.social.audit'].create({
                'action_type': 'publish',
                'user_id': self.env.user.id,
                'partner_id': schedule.partner_id.id,
                'social_account_id': schedule.social_account_id.id,
                'post_id': schedule.post_id.id,
                'result': 'failure',
                'details': {'error': error_msg},
            })
        except:
            pass   # Don't let audit failure break publishing

    def process_webhook_events(self):
        _logger.info("JX Social: process_webhook_events not yet implemented")
        return True

    def retry_failed_posts(self):
        _logger.info("JX Social: retry_failed_posts not yet implemented")
        return True