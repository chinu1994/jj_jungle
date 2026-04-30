/** @odoo-module **/

import { KanbanModel } from '@web/views/kanban/kanban_model';

export class StreamPostKanbanModel extends KanbanModel {

    /**
     * Method responsible for refreshing the configured streams.
     * It will be called on view loading as well as when the user clicks on the 'Refresh' button.
     *
     * @private
     */
    _refreshStreams() {
        return this.orm.silent.call('jj.social.stream', 'refresh_all', []);
    }

    /**
     * Method responsible for refreshing the 'dashboard' view of jj.social.accounts.
     * It will be called on view loading as well as when the user clicks on the 'Refresh' button.
     *
     * Also refreshes live.post statistics (for 'engagement' field).
     *
     * @private
     */
    _refreshAccountsStats() {
        this.orm.silent.call('jj.social.live.post', 'refresh_statistics', []);
        return this.orm.silent.call('jj.social.account', 'refresh_statistics', []);
    }

    /**
     * Will load the jj.social.account statistics that are used to populate the dashboard on
     * top of the 'Feed' (jj.social.stream.post grouped by 'stream_id') kanban view.
     *
     * @private
     */
    _loadAccountsStats() {
        return this.orm.searchRead('jj.social.account',
            [['has_account_stats', '=', true]],
            [
                'id',
                'name',
                'is_media_disconnected',
                'audience',
                'audience_trend',
                'engagement',
                'engagement_trend',
                'stories',
                'stories_trend',
                'has_trends',
                'media_id',
                'media_type',
                'stats_link',
                'image',
        ]);
    }

    /**
     * See 'StreamPostKanbanRenderer#showNoContentHelper'
     * @override
     */
    hasData() {
        return this.root.records.length > 0;
    }

}
