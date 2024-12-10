/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { FormController } from "@web/views/form/form_controller";

export class ResourceFormController extends FormController {
    /**
     * @override
     */
    get archiveDialogProps() {
        let result = super.archiveDialogProps;
        result.body = _t("Archivar este recurso transformará todos sus turnos futuros en turnos abiertos. Estás seguro de que quieres continuar?");
        return result;
    }
}
