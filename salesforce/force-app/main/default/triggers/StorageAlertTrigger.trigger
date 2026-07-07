trigger StorageAlertTrigger on Storage_Alert__c (after insert) {
    StorageAlertTriggerHandler.handleAfterInsert(Trigger.new);
}
