/** @odoo-module **/

import { Component } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const cogMenuRegistry = registry.category("cogMenu");

/**
 * @extends Component
 */
export class FetchImportResPartner extends Component {
    static template = "import_partner_it.FetchImportResPartner";
    static components = { DropdownItem };

    setup() {
        this.action = useService("action");
    }

    async openFetchImportResPartner() {

        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: ('Importar Partner'),
            target: 'new',
            res_model: 'import.partner.it',
            views: [[false, 'form']],
        });
      
    }
}

export const FetchImportResPartnerItem = {
    Component: FetchImportResPartner,
    groupNumber: 5,
    isDisplayed: ({ config, isSmall }) => {
        return !isSmall &&
        config.actionType === "ir.actions.act_window" &&
        ["list"].includes(config.viewType) &&
        ["res_partner_list"].includes(config.viewSubType);
    },
};

cogMenuRegistry.add("fetch-missing-transaction-menu-respartner", FetchImportResPartnerItem, { sequence: 1 });
