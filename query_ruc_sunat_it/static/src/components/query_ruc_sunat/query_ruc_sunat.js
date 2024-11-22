/** @odoo-module **/

import { Component } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const cogMenuRegistry = registry.category("cogMenu");

/**
 * @extends Component
 */
export class FetchImportQueryRucSunat extends Component {
    static template = "query_ruc_sunat_it.FetchImportQueryRucSunat";
    static components = { DropdownItem };

    setup() {
        this.action = useService("action");
    }

    async openFetchImportQueryRucSunat() {

        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: ('Consulta Masiva'),
            target: 'new',
            res_model: 'query.ruc.sunat.wizard.masiva.it',
            views: [[false, 'form']],
        });
      
    }
}

export const FetchImportQueryRucSunatItem = {
    Component: FetchImportQueryRucSunat,
    groupNumber: 5,
    isDisplayed: ({ config, isSmall }) => {
        return !isSmall &&
        config.actionType === "ir.actions.act_window" &&
        ["list"].includes(config.viewType) &&
        ["query_ruc_sunat_list"].includes(config.viewSubType);
    },
};

cogMenuRegistry.add("fetch-missing-transaction-menu-queryrucsunat", FetchImportQueryRucSunatItem, { sequence: 1 });
