/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';
import { one } from '@mail/model/model_field';

registerPatch({
    name: 'Messaging',
    fields: {
        /**
         * Registers the system singleton 'JJ_Junglesocial' in global messaging
         * singleton.
         */
        JJ_Junglesocial: one('JJ_Junglesocial', {
            default: {},
            readonly: true,
            required: true,
        }),
    },
});
