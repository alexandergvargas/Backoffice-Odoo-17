/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { markup, useEnv, onWillUnmount } from "@odoo/owl";
import { serializeDateTime } from "@web/core/l10n/dates";
import { useService } from "@web/core/utils/hooks";
import { escape } from "@web/core/utils/strings";

/**
 * @param {Object} params
 * @param {() => any} params.getAdditionalContext
 * @param {() => any} params.getDomain
 * @param {() => any} params.getRecords
 * @param {() => any} params.getResModel
 * @param {() => luxon.DateTime} params.getStartDate
 * @param {() => any} params.toggleHighlightPlannedFilter
 * @param {() => Promise<any>} params.reload
 */
export class PlanningControllerActions {
    constructor({
        getAdditionalContext,
        getDomain,
        getRecords,
        getResModel,
        getStartDate,
        toggleHighlightPlannedFilter,
        reload,
    }) {
        this.getAdditionalContext = getAdditionalContext;
        this.getDomain = getDomain;
        this.getRecords = getRecords;
        this.getResModel = getResModel;
        this.getStartDate = getStartDate;
        this.toggleHighlightPlannedFilter = toggleHighlightPlannedFilter;
        this.reload = reload;
        this.actionService = useService("action");
        this.env = useEnv();
        this.notifications = useService("notification");
        this.orm = useService("orm");
    }

    async copyPrevious() {
        const resModel = this.getResModel();
        const startDate = serializeDateTime(this.getStartDate());
        const domain = this.getDomain();
        const result = await this.orm.call(resModel, "action_copy_previous_week", [
            startDate,
            domain,
        ]);
        if (result) {
            const notificationRemove = this.notifications.add(
                markup(
                    `<i class="fa fa-fw fa-check"></i><span class="ms-1">${escape(_t(
                        "Se han copiado exitosamente los turnos de la semana anterior."
                    ))}</span>`
                ),
                {
                    type: "success",
                    sticky: true,
                    buttons: [{
                        name: 'Deshacer',
                        icon: 'fa-undo',
                        onClick: async () => {
                            await this.orm.call(
                                resModel,
                                'action_rollback_copy_previous_week',
                                result,
                            );
                            this.toggleHighlightPlannedFilter(false);
                            this.notifications.add(
                                markup(
                                    `<i class="fa fa-fw fa-check"></i><span class="ms-1">${escape(_t(
                                        "Se han eliminado con éxito los turnos que se habían copiado de la semana anterior."
                                    ))}</span>`
                                ),
                                { type: 'success' },
                            );
                            notificationRemove();
                        },
                    }],
                }
            );
            this.toggleHighlightPlannedFilter(result[0]);

            this.notificationFn = notificationRemove;

        } else {
            this.notifications.add(
                _t(
                    "No hay turnos previstos para la semana anterior o ya han sido copiados."
                ),
                { type: "danger" }
            );
        }
    }

    async publish() {
        const records = this.getRecords();
        if (!records?.length) {
            return this.notifications.add(
                _t(
                    "Los turnos ya fueron publicados, o no hay turnos para publicar."
                ),
                { type: "danger" }
            );
        }
        // return this.actionService.doAction("hr_assistance_planning.planning_send_action", {
        //     additionalContext: this.getAdditionalContext(),
        //     onClose: this.reload,
        // });
    }
}

export function usePlanningControllerActions() {
    const planningControllerActions = new PlanningControllerActions(...arguments);

    onWillUnmount(() => {
        planningControllerActions.notificationFn?.();
    });

    return planningControllerActions;
}

export function usePlanningModelActions({
    getHighlightPlannedIds,
    getContext,
}) {
    const orm = useService("orm");
    return {
        async getHighlightIds() {
            const context = getContext();
            if (!context.highlight_conflicting && !context.highlight_planned) {
                return;
            }

            if (context.highlight_conflicting) {
                const highlightConflictingIds = await orm.search(
                    "hr.assistance.planning.line",
                    [["overlap_slot_count", ">", 0]],
                );

                if (context.highlight_planned) {
                    return Array.from(
                        new Set([...highlightConflictingIds, ...getHighlightPlannedIds()])
                    );
                }
                return highlightConflictingIds;
            }
            return getHighlightPlannedIds() || [];
        },
    };
}
