/** @odoo-module **/

import { KanbanRenderer } from '@web/views/kanban/kanban_renderer';

import { StreamPostKanbanRecord } from './jj_jungle_stream_post_kanban_record';

export class StreamPostKanbanRenderer extends KanbanRenderer {

    /**
     * Always display the no-content helper, even if there are groups.
     */
    get showNoContentHelper() {
        const { model } = this.props.list;
        return !model.hasData();
    }

}

StreamPostKanbanRenderer.template = 'JJ_Junglesocial.KanbanRenderer';
StreamPostKanbanRenderer.components = {
    ...KanbanRenderer.components,
    KanbanRecord: StreamPostKanbanRecord,
};
