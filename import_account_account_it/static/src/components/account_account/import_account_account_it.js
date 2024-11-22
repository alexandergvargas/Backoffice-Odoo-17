/** @odoo-module **/

import { Component } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const cogMenuRegistry = registry.category("cogMenu");

/**
 * @extends Component
 */
export class FetchImportAccountAccount extends Component {
    static template = "import_account_account_it.FetchImportAccountAccount";
    static components = { DropdownItem };

    setup() {
        this.action = useService("action");
    }

    async openFetchImportAccountAccount() {         
        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: ('Importar Plan contable'),
            target: 'new',
            res_model: 'import.account.wizard',
            views: [[false, 'form']],
        });
      
    }
}

export const FetchImportAccountAccountItem = {
    Component: FetchImportAccountAccount,
    groupNumber: 5,
    isDisplayed: ({ config, isSmall }) => {
        return !isSmall &&
        config.actionType === "ir.actions.act_window" &&
        ["list"].includes(config.viewType) &&
        ["account_account_list"].includes(config.viewSubType);
    },
};

cogMenuRegistry.add("fetch-missing-transaction-menu-account", FetchImportAccountAccountItem, { sequence: 1 });
