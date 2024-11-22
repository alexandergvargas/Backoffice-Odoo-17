/** @odoo-module **/

import { Component } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const cogMenuRegistry = registry.category("cogMenu");

/**
 * @extends Component
 */
export class FetchImportAccountMove extends Component {
    static template = "import_invoice.FetchImportAccountMove";
    static components = { DropdownItem };

    setup() {
        this.action = useService("action");
    }

    async openFetchImportAccountMove() {         
        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Importar Facturas',
            res_model: 'import.invoice.it',
            views: [
                [false, 'tree'],  
                [false, 'form']   
            ],
            target: 'current',  
        });
    }
    
}

export const FetchImportAccountMoveItem = {
    Component: FetchImportAccountMove,
    groupNumber: 5,
    isDisplayed: ({ config, isSmall }) => {
        return !isSmall &&
        config.actionType === "ir.actions.act_window" &&
        ["list"].includes(config.viewType) &&
        ["account_tree"].includes(config.viewSubType);
    },
};

cogMenuRegistry.add("fetch-missing-transaction-menu-accountmove", FetchImportAccountMoveItem, { sequence: 1 });
