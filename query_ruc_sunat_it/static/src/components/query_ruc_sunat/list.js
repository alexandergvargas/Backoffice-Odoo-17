/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";


export class QueryRucSunatListController extends ListController {

    setup() {
        super.setup(...arguments);     
    }
}

export const QueryRucSunatListView = {
    ...listView,
    Controller: QueryRucSunatListController,
}

registry.category("views").add("query_ruc_sunat_list", QueryRucSunatListView);
