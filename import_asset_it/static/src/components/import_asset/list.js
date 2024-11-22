/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";


export class AssetListController extends ListController {

    setup() {
        super.setup(...arguments);     
    }
}

export const AssetListView = {
    ...listView,
    Controller: AssetListController,
}

registry.category("views").add("asset_list", AssetListView);
