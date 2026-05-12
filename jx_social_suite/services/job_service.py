# -*- coding: utf-8 -*-

from odoo import models, fields, api
from .registry import get_connector
import logging



_logger = logging.getLogger(__name__)

class JxSocialJobService(models.AbstractModel):
    _name = 'jx.social.job.service'
    _description = 'JX Social Job Queue & Publishing Service'

    # ===================================================================
    # 7.3 publish_queued_posts - Cron Handler (Most Critical Method)
    # ===================================================================

    @api.model
    def publish_queued_posts(self):
        """
        Main cron job handler as per Section 7.3
        Processes up to 50 queued posts with individual commits.
        """
        _logger.info("JX Social: Starting publish_queued_posts cron")

        # 24. Query as per documentation
        schedules = self.env['jx.social.schedule'].search([
            ('state', '=', 'queued'),
            ('scheduled_at', '<=', fields.Datetime.now())
        ], order='scheduled_at ASC', limit=50)

        if not schedules:
            return

        for schedule in schedules:
            try:
                # Use no_recompute context as specified
                schedule = schedule.with_context(no_recompute=True)

                # 26. Set to 'publishing' BEFORE calling API (prevent duplicate execution)
                schedule.write({'state': 'publishing'})

                # Force commit immediately after status change
                self.env.cr.commit()

                # 27. Get connector and publish
                connector = get_connector(
                    self.env,
                    schedule.social_account_id.provider
                )

                result = connector.publish_post(schedule)

                # 28. On Success
                if result and result.get('external_post_id'):
                    schedule.write({
                        'state': 'sent',
                        'external_post_id': result.get('external_post_id'),
                        'published_at': result.get('published_at') or fields.Datetime.now(),
                        'provider_response': str(result.get('raw_response', {}))
                    })
                else:
                    raise Exception("Publish returned no external_post_id")

            except Exception as e:
                # 29. On Failure
                error_msg = str(e)
                _logger.error("Failed to publish schedule %s: %s", schedule.id, error_msg)

                try:
                    schedule.write({
                        'state': 'failed',
                        'error_message': error_msg[:500],  # truncate
                        'retry_count': schedule.retry_count + 1,
                    })
                except:
                    _logger.error("Failed to update schedule %s after error", schedule.id)

                # Write to audit log (will be implemented in audit service)
                self._log_publish_error(schedule, error_msg)

            finally:
                # 30. Individual commit after each record
                try:
                    self.env.cr.commit()
                except Exception as commit_error:
                    _logger.error("Commit failed for schedule %s: %s", schedule.id, commit_error)

        _logger.info("JX Social: Completed publish_queued_posts run. Processed: %s", len(schedules))