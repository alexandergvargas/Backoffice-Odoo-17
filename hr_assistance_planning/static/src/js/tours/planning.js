/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { markup } from "@odoo/owl";

registry.category("web_tour.tours").add('planning_tour', {
    sequence: 120,
    url: '/web',
    rainbowManMessage: () => markup(_t("<b>Felicitaciones!</b></br> Ahora eres un experto de la planificación.")),
    steps: () => [
    {
        trigger: '.o_app[data-menu-xmlid="hr_assistance_planning.planning_menu_root"]',
        content: markup(_t("¡Empecemos a gestionar los horarios de tus empleados!")),
        position: 'bottom',
    }, {
        trigger: ".o_gantt_button_add",
        content: markup(_t("Vamos a crear tu primer <b>Turno</b>. <i>Consejo: utilice el acceso directo (+) disponible en cada celda de la vista Gantt para ahorrar tiempo.</i>")),
        position: "bottom",
    }, {
        trigger: ".o_field_widget[name='resource_id']",
        content: markup(_t("Asignar un <b>empleado</b>, O dejala abierta por el momento. <i>Consejo: cree turnos abiertos para los roles que necesitará para completar un horario. Luego, asigna esos turnos abiertos a los empleados que estén disponibles.</i>")),
        position: "right",
    }, {
        trigger: ".o_field_widget[name='role_id'] .o_field_many2one_selection",
        content: markup(_t("Escribe el <b>turno</b> Tu empleado realizará (<i>Ejemplo. Mañana, Tarde, Noche, etc.</i>). <i>Consejo: cree turnos abiertos para los turnos que necesitará para completar un horario. Luego, asigna esos turnos abiertos a los empleados que estén disponibles.</i>")),
        position: "right",
    }, {
        trigger: "button[special='save']",
        content: _t("Guarde este turno una vez que esté listo."),
        position: "bottom",
    }, {
        trigger: ".o_gantt_pill:not(.o_gantt_consolidated_pill)",
        extra_trigger: '.o_action:not(.o_view_sample_data)',
        content: markup(_t("<b>Arrastrar y soltar</b> tu turno para reprogramarlo. <i>Consejo: presione CTRL (o Cmd) para duplicarlo.</i> <b>Ajustar el tamaño</b> del turno para modificar su período.")),
        position: "bottom",
        run: "drag_and_drop_native .o_gantt_cell:nth-child(6)",
    }, {
        trigger: ".o_gantt_button_send_all",
        content: markup(_t("Si está conforme con su planificación, ahora puede <b>Publicar</b> sus horarios.")),
        position: "bottom",
    }, {
        trigger: "button[name='action_check_emails']",
        content: markup(_t("<b>Publicar</b> la planificación de su empleado.")),
        position: "bottom",
    }, {
        trigger: "button.o_gantt_button_next",
        extra_trigger: "body:not(.modal-open)",
        content: markup(_t("Ahora que esta semana está lista, comencemos <b>con el horario de la próxima semana</b>.")),
        position: "bottom",
    }, {
        trigger: "button.o_gantt_button_copy_previous_week",
        content: markup(_t("Planifica todos tus turnos con un solo clic <b>copiando el horario de la semana anterior</b>.")),
        position: "bottom",
    },
]});
