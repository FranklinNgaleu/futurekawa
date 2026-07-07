public class StorageAlertTriggerHandler {

    public static void handleAfterInsert(List<Storage_Alert__c> newAlerts) {
        Set<Id> lotIds = new Set<Id>();
        List<Storage_Alert__c> expiredAlerts = new List<Storage_Alert__c>();

        for (Storage_Alert__c alert : newAlerts) {
            if (alert.Alert_Type__c == 'LOT_EXPIRED' && alert.Handled__c == false) {
                expiredAlerts.add(alert);
                if (alert.Coffee_Lot__c != null) {
                    lotIds.add(alert.Coffee_Lot__c);
                }
            }
        }

        if (expiredAlerts.isEmpty()) {
            return;
        }

        Map<Id, Coffee_Lot__c> lotsById = new Map<Id, Coffee_Lot__c>();
        if (!lotIds.isEmpty()) {
            lotsById = new Map<Id, Coffee_Lot__c>([SELECT Id, OwnerId FROM Coffee_Lot__c WHERE Id IN :lotIds]);
        }

        List<Task> tasksToInsert = new List<Task>();
        for (Storage_Alert__c alert : expiredAlerts) {
            Task expeditionTask = new Task();
            expeditionTask.Subject = 'Expédier en priorité (FIFO) - lot périmé';
            expeditionTask.Status = 'Not Started';
            expeditionTask.Priority = 'High';

            Coffee_Lot__c relatedLot = alert.Coffee_Lot__c != null ? lotsById.get(alert.Coffee_Lot__c) : null;
            if (relatedLot != null) {
                expeditionTask.WhatId = relatedLot.Id;
                expeditionTask.OwnerId = relatedLot.OwnerId;
            } else {
                expeditionTask.OwnerId = UserInfo.getUserId();
            }

            tasksToInsert.add(expeditionTask);
        }

        insert tasksToInsert;
    }
}
