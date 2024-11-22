/** @odoo-module **/

import { Component } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const cogMenuRegistry = registry.category("cogMenu");

/**
 * @extends Component
 */
export class FetchImportAsset extends Component {
    static template = "import_asset_it.FetchImportAsset";
    static components = { DropdownItem };

    setup() {
        this.action = useService("action");
    }

    async openFetchImportAsset() {

        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: ('Importar Activos'),
            target: 'new',
            res_model: 'import.asset.wizard',
            views: [[false, 'form']],
        });
      
    }
}

export const FetchImportAssetItem = {
    Component: FetchImportAsset,
    groupNumber: 5,
    isDisplayed: ({ config, isSmall }) => {
        return !isSmall &&
        config.actionType === "ir.actions.act_window" &&
        ["list"].includes(config.viewType) &&
        ["asset_list"].includes(config.viewSubType);
    },
};

cogMenuRegistry.add("fetch-missing-transaction-menu-asset", FetchImportAssetItem, { sequence: 1 });
