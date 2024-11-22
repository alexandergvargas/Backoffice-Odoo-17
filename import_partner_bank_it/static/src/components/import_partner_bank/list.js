/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";


export class ResPartnerBankListController extends ListController {

    setup() {
        super.setup(...arguments);     
    }
}

export const ResPartnerBankListView = {
    ...listView,
    Controller: ResPartnerBankListController,
}

registry.category("views").add("res_partner_bank_list", ResPartnerBankListView);
