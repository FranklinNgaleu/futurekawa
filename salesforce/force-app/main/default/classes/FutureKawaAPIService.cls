public class FutureKawaAPIService {

    public static void syncAll() {
        syncLots();
        syncAlerts();
    }

    public static void syncLots() {
        HttpResponse response = performCallout('/lots');
        if (response == null || response.getStatusCode() != 200) {
            return;
        }

        List<Object> payload = (List<Object>) JSON.deserializeUntyped(response.getBody());
        List<Coffee_Lot__c> lotsToUpsert = new List<Coffee_Lot__c>();

        for (Object item : payload) {
            Map<String, Object> lot = (Map<String, Object>) item;
            Coffee_Lot__c record = new Coffee_Lot__c();
            record.Lot_Code__c = (String) lot.get('lot_code');
            record.Country__c = normalizeCountry((String) lot.get('country'));
            record.Warehouse__c = (String) lot.get('warehouse');
            record.Status__c = normalizeStatus((String) lot.get('status'));

            Object storageDate = lot.get('storage_date');
            if (storageDate != null) {
                record.Storage_Date__c = parseDate((String) storageDate);
            }

            lotsToUpsert.add(record);
        }

        if (!lotsToUpsert.isEmpty()) {
            // allOrNone=false: one malformed upstream lot must not block the rest of the sync batch
            Database.upsert(lotsToUpsert, Coffee_Lot__c.Lot_Code__c, false);
        }
    }

    public static void syncAlerts() {
        HttpResponse response = performCallout('/alerts');
        if (response == null || response.getStatusCode() != 200) {
            return;
        }

        List<Object> payload = (List<Object>) JSON.deserializeUntyped(response.getBody());
        Set<String> lotCodes = new Set<String>();

        for (Object item : payload) {
            Map<String, Object> alert = (Map<String, Object>) item;
            Object lotCode = alert.get('lot_code');
            if (lotCode != null) {
                lotCodes.add((String) lotCode);
            }
        }

        Map<String, Id> lotIdsByCode = new Map<String, Id>();
        if (!lotCodes.isEmpty()) {
            for (Coffee_Lot__c lot : [SELECT Id, Lot_Code__c FROM Coffee_Lot__c WHERE Lot_Code__c IN :lotCodes]) {
                lotIdsByCode.put(lot.Lot_Code__c, lot.Id);
            }
        }

        List<Storage_Alert__c> alertsToInsert = new List<Storage_Alert__c>();
        for (Object item : payload) {
            Map<String, Object> alert = (Map<String, Object>) item;
            Storage_Alert__c record = new Storage_Alert__c();
            record.Alert_Type__c = (String) alert.get('type');
            record.Warehouse__c = (String) alert.get('warehouse');
            record.Handled__c = false;

            String message = (String) alert.get('message');
            if (message != null && message.length() > 255) {
                message = message.substring(0, 255);
            }
            record.Message__c = message;

            Object value = alert.get('value');
            if (value != null) {
                record.Value__c = parseDecimal(value);
            }

            Object timestamp = alert.get('timestamp');
            if (timestamp != null) {
                record.Alert_Timestamp__c = parseDateTime((String) timestamp);
            }

            // lot_code is not part of the documented /alerts payload; when present it lets us link the alert to its lot
            Object lotCode = alert.get('lot_code');
            if (lotCode != null && lotIdsByCode.containsKey((String) lotCode)) {
                record.Coffee_Lot__c = lotIdsByCode.get((String) lotCode);
            }

            alertsToInsert.add(record);
        }

        if (!alertsToInsert.isEmpty()) {
            insert alertsToInsert;
        }
    }

    private static HttpResponse performCallout(String path) {
        try {
            HttpRequest request = new HttpRequest();
            request.setEndpoint('callout:FutureKawa_API' + path);
            request.setMethod('GET');
            return new Http().send(request);
        } catch (Exception e) {
            // network/timeout/DNS failures must not break the scheduled sync job
            return null;
        }
    }

    private static String normalizeCountry(String rawCountry) {
        if (rawCountry == null) {
            return null;
        }
        String lower = rawCountry.toLowerCase();
        if (lower.contains('bresil') || lower.contains('brésil') || lower == 'brazil') {
            return 'Brésil';
        }
        if (lower.contains('equateur') || lower.contains('équateur') || lower == 'ecuador') {
            return 'Équateur';
        }
        if (lower.contains('colombie') || lower == 'colombia') {
            return 'Colombie';
        }
        return rawCountry;
    }

    private static String normalizeStatus(String rawStatus) {
        if (rawStatus == null) {
            return null;
        }
        String lower = rawStatus.toLowerCase();
        if (lower == 'conforme') {
            return 'Conforme';
        }
        if (lower == 'en alerte') {
            return 'En alerte';
        }
        if (lower == 'périmé' || lower == 'perime') {
            return 'Périmé';
        }
        return rawStatus;
    }

    private static Date parseDate(String isoDate) {
        try {
            return Date.valueOf(isoDate.length() > 10 ? isoDate.substring(0, 10) : isoDate);
        } catch (Exception e) {
            return null;
        }
    }

    private static DateTime parseDateTime(String isoDateTime) {
        try {
            String cleaned = isoDateTime.endsWith('Z') ? isoDateTime.substring(0, isoDateTime.length() - 1) : isoDateTime;
            List<String> dateTimeParts = cleaned.split('T');
            List<String> dateParts = dateTimeParts[0].split('-');
            List<String> timeParts = dateTimeParts[1].split(':');
            String secondsPart = timeParts[2];
            Integer seconds = Integer.valueOf(secondsPart.contains('.') ? secondsPart.substringBefore('.') : secondsPart);

            return DateTime.newInstanceGMT(
                Integer.valueOf(dateParts[0]),
                Integer.valueOf(dateParts[1]),
                Integer.valueOf(dateParts[2]),
                Integer.valueOf(timeParts[0]),
                Integer.valueOf(timeParts[1]),
                seconds
            );
        } catch (Exception e) {
            return null;
        }
    }

    private static Decimal parseDecimal(Object value) {
        try {
            return Decimal.valueOf(String.valueOf(value));
        } catch (Exception e) {
            return null;
        }
    }
}
