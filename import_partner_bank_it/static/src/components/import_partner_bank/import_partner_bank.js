/** @odoo-module **/

import { Component } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const cogMenuRegistry = registry.category("cogMenu");

/**
 * @extends Component
 */
export class FetchImportResPartnerBank extends Component {
    static template = "import_partner_bank_it.FetchImportResPartnerBank";
    static components = { DropdownItem };

    setup() {
        this.action = useService("action");
    }

    async openFetchImportResPartnerBank() {

        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: ('Importar Cuentas Bancarias'),
            target: 'new',
            res_model: 'import.partner.bank.it',
            views: [[false, 'form']],
        });
      
    }
}

export const FetchImportResPartnerBankItem = {
    Component: FetchImportResPartnerBank,
    groupNumber: 5,
    isDisplayed: ({ config, isSmall }) => {
        return !isSmall &&
        config.actionType === "ir.actions.act_window" &&
        ["list"].includes(config.viewType) &&
        ["res_partner_bank_list"].includes(config.viewSubType);
    },
};

cogMenuRegistry.add("fetch-missing-transaction-menu-respartnerbank", FetchImportResPartnerBankItem, { sequence: 1 });
