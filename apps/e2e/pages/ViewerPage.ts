import type { Locator, Page } from '@playwright/test';
import { BASE_URL } from '../specs/common.helpers';

export class ViewerPage {
    constructor(private readonly page: Page) {}

    get headers(): Locator { return this.page.locator('#job-table thead th'); }
    get divider(): Locator { return this.page.locator('#panel-divider'); }
    get resizeHandle(): Locator { return this.page.locator('#panel-resize-handle'); }
    get collapseListButton(): Locator { return this.page.locator('#panel-collapse-list'); }
    get collapseDetailButton(): Locator { return this.page.locator('#panel-collapse-detail'); }
    get resetButton(): Locator { return this.page.locator('#panel-reset'); }
    get locationHeader(): Locator { return this.page.locator('#job-table-location-header'); }
    get modalityHeader(): Locator { return this.page.locator('#job-table-modality-header'); }
    get detailTitle(): Locator { return this.page.locator('#job-detail-title'); }
    get tabButtons(): Locator { return this.page.locator('#viewer-toolbar .tab-buttons'); }
    get listTab(): Locator { return this.page.locator('#tab-button-list'); }
    get editTab(): Locator { return this.page.locator('#tab-button-edit'); }
    get createTab(): Locator { return this.page.locator('#tab-button-create'); }
    get detailPanel(): Locator { return this.page.locator('#viewer-right'); }

    jobRow(id: number): Locator { return this.page.locator(`#job-row-${id}`); }
    locationCell(id: number): Locator { return this.page.locator(`#job-location-${id}`); }
    modalityBadges(id: number): Locator { return this.page.locator(`#job-modality-${id} .modality-badge`); }

    async open(): Promise<void> {
        await this.page.goto(BASE_URL);
        await this.jobRow(1).waitFor();
    }

    async selectJob(id: number): Promise<void> {
        await this.jobRow(id).click();
    }

    async storedRatio(): Promise<string | null> {
        return this.page.evaluate(() => localStorage.getItem('viewer-list-ratio'));
    }
}
