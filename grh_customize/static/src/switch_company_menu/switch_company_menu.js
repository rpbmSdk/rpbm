/** @odoo-module **/

import { patch } from "@web/core/utils/patch";

import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";

patch(SwitchCompanyMenu.prototype, {

    toogleAllCompanies() {
        console.log("toogleAllCompanies");
        let companyIds = []
        for (const companyKey in this.companyService.allowedCompanies) {
            const company = this.companyService.allowedCompanies[companyKey];
            companyIds.push(company.id);
        }
        this.companyService.setCompanies(companyIds, true);
    }
});
