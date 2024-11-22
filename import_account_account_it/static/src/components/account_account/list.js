/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";

import { useChildSubEnv } from "@odoo/owl";

export class AccountAccountListController extends ListController {

    setup() {
        super.setup(...arguments);
       
    }
   
}

export const AccountAccountListView = {
    ...listView,
    Controller: AccountAccountListController,
}

registry.category("views").add("account_account_list", AccountAccountListView);
