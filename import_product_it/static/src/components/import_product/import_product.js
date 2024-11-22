/** @odoo-module **/

import { Component } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const cogMenuRegistry = registry.category("cogMenu");

/**
 * @extends Component
 */
export class FetchImportProductTemplate extends Component {
    static template = "import_product_it.FetchImportProductTemplate";
    static components = { DropdownItem };

    setup() {
        this.action = useService("action");
    }

    async openFetchImportProductTemplate() {

        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: ('Importar Producto'),
            target: 'new',
            res_model: 'import.product.it',
            views: [[false, 'form']],
        });
      
    }
}

export const FetchImportProductTemplateItem = {
    Component: FetchImportProductTemplate,
    groupNumber: 5,
    isDisplayed: ({ config, isSmall }) => {
        return !isSmall &&
        config.actionType === "ir.actions.act_window" &&
        ["list"].includes(config.viewType) &&
        ["product_list"].includes(config.viewSubType);
    },
};

cogMenuRegistry.add("fetch-missing-transaction-menu-producttemplate", FetchImportProductTemplateItem, { sequence: 1 });
