/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";


export class ProductTemplateListController extends ListController {

    setup() {
        super.setup(...arguments);     
    }
}

export const ProductTemplateListView = {
    ...listView,
    Controller: ProductTemplateListController,
}

registry.category("views").add("product_list", ProductTemplateListView);
