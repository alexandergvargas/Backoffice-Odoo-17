/** @odoo-module **/

import { Component } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const cogMenuRegistry = registry.category("cogMenu");

/**
 * @extends Component
 */
export class FetchImportStatementLine extends Component {
    static template = "account_bank_statement_import_it.FetchImportStatementLine";
    static components = { DropdownItem };

    setup() {
        this.action = useService("action");
    }

    async openFetchImportStatementLineWizard() {
        const { context } = this.env.searchModel;
        const activeModel = context.active_model;
        let activeIds = [];
        console.log(context)
        if (activeModel === "account.bank.statement") {
            activeIds = context.active_ids;
        } else if (!!context.default_statement_id) {
            activeIds = context.default_statement_id;
        }
       
        const action = await this.env.services.orm.call(
            "account.bank.statement",
            "action_import_lines",
            [activeIds]
        );
        return this.action.doAction(action);
    }
}

export const FetchImportStatementLineItem = {
    Component: FetchImportStatementLine,
    groupNumber: 5,
    isDisplayed: ({ config, isSmall }) => {
        return !isSmall &&
        config.actionType === "ir.actions.act_window" &&
        ["kanban", "list"].includes(config.viewType) &&
        ["bank_rec_widget_kanban", "bank_rec_list"].includes(config.viewSubType);
    },
};

cogMenuRegistry.add("fetch-missing-transaction-menu-new", FetchImportStatementLineItem, { sequence: 1 });
