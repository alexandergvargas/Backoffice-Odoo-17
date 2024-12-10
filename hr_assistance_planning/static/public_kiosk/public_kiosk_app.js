/** @odoo-module **/

import {App, whenReady, Component, useState} from "@odoo/owl";
import { CardLayout } from "@hr_attendance/components/card_layout/card_layout";
import { KioskManualSelection } from "@hr_attendance/components/manual_selection/manual_selection";
import { makeEnv, startServices } from "@web/env";
import { templates } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { MainComponentsContainer } from "@web/core/main_components_container";
import { useService, useBus } from "@web/core/utils/hooks";
import { url } from "@web/core/utils/urls";
import {KioskGreetings} from "@hr_attendance/components/greetings/greetings";
import {KioskPinCode} from "@hr_attendance/components/pin_code/pin_code";
import {KioskBarcodeScanner} from "@hr_attendance/components/kiosk_barcode/kiosk_barcode";

class kioskAttendanceAppExtend extends Component{
    static props = [];
    static components = {
        KioskBarcodeScanner,
        CardLayout,
        KioskManualSelection,
        KioskGreetings,
        KioskPinCode,
        MainComponentsContainer,
    };

    setup() {
        this.rpc = useService("rpc");
        this.barcode = useService("barcode");
        this.notification = useService("notification");
        this.companyImageUrl = url("/web/binary/company_logo", {
            company: this.props.companyId,
        });
        this.lockScanner = false;
        if (this.props.kioskMode !== 'manual'){
            useBus(this.barcode.bus, "barcode_scanned", (ev) => this.onBarcodeScanned(ev.detail.barcode));
            this.state = useState({active_display: "main"});
            this.manualKioskMode = false
        }else{
            this.manualKioskMode = true
            this.state = useState({active_display: "manual"});
        }
    }

    switchDisplay(screen) {
        const displays = ["main", "greet", "manual", "pin"]
        if (displays.includes(screen)){
            this.state.active_display = screen;
        }else{
            this.state.active_display = "main";
        }
    }

    async kioskConfirm(employeeId){
        const employee = await this.rpc('attendance_employee_data',
            {
                'token': this.props.token,
                'employee_id': employeeId
            })
        if (employee && employee.employee_name){
            if (employee.use_pin){
                this.employeeData = employee
                this.switchDisplay('pin')
            }else{
                await this.onManualSelection(employeeId, false)
            }
        }
    }

    kioskReturn() {
        if (this.props.kioskMode !== 'manual'){
            this.switchDisplay('main')
        }else{
            this.switchDisplay('manual')
        }
    }

    displayNotification(text){
        this.notification.add(text, { type: "danger" });
    }

    updateActivity(ev) {
    this.state.selectedActivity = ev.target.value;
    // console.log(`selectedActivity: ${this.state.selectedActivity}`);
    this.render();
    }

    async onManualSelection(employeeId, enteredPin){
        const activityId = this.state.selectedActivity;
        const result = await this.rpc('manual_selection',
            {
                'token': this.props.token,
                'employee_id': employeeId,
                'pin_code': enteredPin,
                'assistance_planning_id':activityId
            })
        // console.log(`result onManualSelection: ${result.attendance}`);
        if (result && result.attendance) {
            this.employeeData = result
            this.switchDisplay('greet')
        }else{
            if (enteredPin){
                this.displayNotification(_t("Wrong Pin"))
            }
        }
       // console.log(`Employee ID: ${employeeId}, Pin: ${enteredPin}, Tipo_id: ${activityId}`);
    }

    async onBarcodeScanned(barcode){
        if (this.lockScanner || this.state.active_display !== 'main') {
            return;
        }
        this.lockScanner = true;
        const result = await this.rpc('attendance_barcode_scanned',
            {
                'barcode': barcode,
                'token': this.props.token
            })
        if (result && result.employee_name) {
            this.employeeData = result
            this.switchDisplay('greet')
        }else{
            this.displayNotification(_t("No employee corresponding to Badge ID '%(barcode)s.'", { barcode }))
        }
        this.lockScanner = false
    }
}

kioskAttendanceAppExtend.template = "hr_attendance.public_kiosk_app";

export async function createPublicKioskAttendanceExtend(document, kiosk_backend_info) {
    await whenReady();
    const env = makeEnv();
    await startServices(env);
    // console.log(`kiosk_backend_info: ${kiosk_backend_info}`);
    const app = new App(kioskAttendanceAppExtend, {
        templates,
        env: env,
        props:
            {
                token : kiosk_backend_info.token,
                companyId: kiosk_backend_info.company_id,
                companyName: kiosk_backend_info.company_name,
                employees: kiosk_backend_info.employees,
                departments: kiosk_backend_info.departments,
                kioskMode: kiosk_backend_info.kiosk_mode,
                barcodeSource: kiosk_backend_info.barcode_source,
                activities: kiosk_backend_info.activities,
            },
        dev: env.debug,
        translateFn: _t,
        translatableAttributes: ["data-tooltip"],
    });
    // console.log(`app: ${app}`);
    return app.mount(document.body);
}
export default { kioskAttendanceAppExtend, createPublicKioskAttendanceExtend };
