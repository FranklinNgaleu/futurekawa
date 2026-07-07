@isTest
private class StorageAlertTriggerTest {

    @isTest
    static void testExpiredAlertCreatesFifoTaskOnRelatedLot() {
        Coffee_Lot__c lot = new Coffee_Lot__c(
            Lot_Code__c = 'LOT-100',
            Country__c = 'Colombie',
            Warehouse__c = 'WH-Bogota',
            Status__c = 'Périmé',
            Storage_Date__c = Date.today().addDays(-90)
        );
        insert lot;

        Test.startTest();
        Storage_Alert__c alert = new Storage_Alert__c(
            Alert_Type__c = 'LOT_EXPIRED',
            Message__c = 'Lot périmé détecté',
            Value__c = 0,
            Warehouse__c = 'WH-Bogota',
            Alert_Timestamp__c = DateTime.now(),
            Coffee_Lot__c = lot.Id,
            Handled__c = false
        );
        insert alert;
        Test.stopTest();

        List<Task> tasks = [SELECT Subject, Status, Priority, WhatId, OwnerId FROM Task WHERE WhatId = :lot.Id];
        System.assertEquals(1, tasks.size());
        System.assertEquals('Not Started', tasks[0].Status);
        System.assertEquals('High', tasks[0].Priority);
        System.assertEquals(lot.Id, tasks[0].WhatId);
    }

    @isTest
    static void testNonExpiredAlertCreatesNoTask() {
        Coffee_Lot__c lot = new Coffee_Lot__c(
            Lot_Code__c = 'LOT-101',
            Country__c = 'Brésil',
            Warehouse__c = 'WH-Santos',
            Status__c = 'Conforme',
            Storage_Date__c = Date.today().addDays(-5)
        );
        insert lot;

        Test.startTest();
        Storage_Alert__c alert = new Storage_Alert__c(
            Alert_Type__c = 'TEMPERATURE_OUT_OF_RANGE',
            Message__c = 'Température hors plage',
            Value__c = 15.4,
            Warehouse__c = 'WH-Santos',
            Alert_Timestamp__c = DateTime.now(),
            Coffee_Lot__c = lot.Id,
            Handled__c = false
        );
        insert alert;
        Test.stopTest();

        List<Task> tasks = [SELECT Id FROM Task WHERE WhatId = :lot.Id];
        System.assertEquals(0, tasks.size());
    }

    @isTest
    static void testExpiredAlertWithoutLotUsesRunningUserAsOwner() {
        Test.startTest();
        Storage_Alert__c alert = new Storage_Alert__c(
            Alert_Type__c = 'LOT_EXPIRED',
            Message__c = 'Lot périmé sans référence',
            Value__c = 0,
            Warehouse__c = 'WH-Unknown',
            Alert_Timestamp__c = DateTime.now(),
            Handled__c = false
        );
        insert alert;
        Test.stopTest();

        List<Task> tasks = [SELECT OwnerId, WhatId FROM Task WHERE Subject = 'Expédier en priorité (FIFO) - lot périmé' AND WhatId = null];
        System.assertEquals(1, tasks.size());
        System.assertEquals(UserInfo.getUserId(), tasks[0].OwnerId);
    }

    @isTest
    static void testAlreadyHandledExpiredAlertCreatesNoTask() {
        Test.startTest();
        Storage_Alert__c alert = new Storage_Alert__c(
            Alert_Type__c = 'LOT_EXPIRED',
            Message__c = 'Déjà traité',
            Value__c = 0,
            Warehouse__c = 'WH-Unknown',
            Alert_Timestamp__c = DateTime.now(),
            Handled__c = true
        );
        insert alert;
        Test.stopTest();

        List<Task> tasks = [SELECT Id FROM Task WHERE Subject = 'Expédier en priorité (FIFO) - lot périmé'];
        System.assertEquals(0, tasks.size());
    }
}
