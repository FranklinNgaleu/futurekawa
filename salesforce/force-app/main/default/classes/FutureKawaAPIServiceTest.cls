@isTest
private class FutureKawaAPIServiceTest {

    private class LotsAndAlertsMock implements HttpCalloutMock {
        public HTTPResponse respond(HTTPRequest request) {
            HttpResponse response = new HttpResponse();
            response.setStatusCode(200);
            response.setHeader('Content-Type', 'application/json');

            String endpoint = request.getEndpoint();
            String country = extractCountry(endpoint);

            if (endpoint.contains('/lots')) {
                response.setBody(lotsBodyFor(country));
            } else if (endpoint.contains('/alerts')) {
                response.setBody(alertsBodyFor(country));
            } else {
                response.setStatusCode(404);
                response.setBody('{}');
            }

            return response;
        }

        private String extractCountry(String endpoint) {
            Integer idx = endpoint.indexOf('country=');
            if (idx < 0) {
                return '';
            }
            String rest = endpoint.substring(idx + 'country='.length());
            Integer ampIdx = rest.indexOf('&');
            return ampIdx >= 0 ? rest.substring(0, ampIdx) : rest;
        }

        private String lotsBodyFor(String country) {
            if (country == 'bresil') {
                return '{"country":"bresil","lots":[' +
                    '{"lot_code":"LOT-001","country":"bresil","warehouse":"WH-Santos","storage_date":"2026-01-15","status":"conforme"}' +
                ']}';
            }
            if (country == 'equateur') {
                return '{"country":"equateur","lots":[' +
                    '{"lot_code":"LOT-002","country":"equateur","warehouse":"WH-Guayaquil","storage_date":"2025-11-01","status":"périmé"}' +
                ']}';
            }
            return '{"country":"' + country + '","lots":[]}';
        }

        private String alertsBodyFor(String country) {
            if (country == 'bresil') {
                return '{"country":"bresil","alerts":[' +
                    '{"type":"TEMPERATURE_OUT_OF_RANGE","message":"Température hors plage","value":32.5,"min":2,"max":10,"warehouse":"WH-Santos","timestamp":"2026-01-20T09:00:00.000Z","country":"bresil"}' +
                ']}';
            }
            if (country == 'equateur') {
                return '{"country":"equateur","alerts":[' +
                    '{"type":"LOT_EXPIRED","message":"Lot expiré","value":0,"min":0,"max":0,"warehouse":"WH-Guayaquil","timestamp":"2026-01-20T08:00:00.000Z","country":"equateur","lot_code":"LOT-002"}' +
                ']}';
            }
            return '{"country":"' + country + '","alerts":[]}';
        }
    }

    private class ErrorMock implements HttpCalloutMock {
        public HTTPResponse respond(HTTPRequest request) {
            HttpResponse response = new HttpResponse();
            response.setStatusCode(500);
            response.setBody('error');
            return response;
        }
    }

    @isTest
    static void testSyncLotsUpsertsRecordsWithNormalizedValues() {
        Test.setMock(HttpCalloutMock.class, new LotsAndAlertsMock());

        Test.startTest();
        FutureKawaAPIService.syncLots();
        Test.stopTest();

        List<Coffee_Lot__c> lots = [SELECT Lot_Code__c, Country__c, Status__c, Warehouse__c, Storage_Date__c FROM Coffee_Lot__c ORDER BY Lot_Code__c];
        System.assertEquals(2, lots.size());
        System.assertEquals('LOT-001', lots[0].Lot_Code__c);
        System.assertEquals('Brésil', lots[0].Country__c);
        System.assertEquals('Conforme', lots[0].Status__c);
        System.assertEquals(Date.newInstance(2026, 1, 15), lots[0].Storage_Date__c);
        System.assertEquals('LOT-002', lots[1].Lot_Code__c);
        System.assertEquals('Équateur', lots[1].Country__c);
        System.assertEquals('Périmé', lots[1].Status__c);
    }

    @isTest
    static void testSyncAlertsInsertsRecordsAndLinksLot() {
        Coffee_Lot__c existingLot = new Coffee_Lot__c(
            Lot_Code__c = 'LOT-002',
            Country__c = 'Équateur',
            Warehouse__c = 'WH-Guayaquil',
            Status__c = 'Périmé',
            Storage_Date__c = Date.today().addDays(-60)
        );
        insert existingLot;

        Test.setMock(HttpCalloutMock.class, new LotsAndAlertsMock());

        Test.startTest();
        FutureKawaAPIService.syncAlerts();
        Test.stopTest();

        List<Storage_Alert__c> alerts = [SELECT Alert_Type__c, Value__c, Coffee_Lot__c, Handled__c, Alert_Timestamp__c FROM Storage_Alert__c];
        System.assertEquals(2, alerts.size());

        for (Storage_Alert__c alert : alerts) {
            System.assertEquals(false, alert.Handled__c);
            System.assertNotEquals(null, alert.Alert_Timestamp__c);
            if (alert.Alert_Type__c == 'LOT_EXPIRED') {
                System.assertEquals(existingLot.Id, alert.Coffee_Lot__c);
            } else {
                System.assertEquals(null, alert.Coffee_Lot__c);
            }
        }
    }

    @isTest
    static void testSyncAllHandlesNon200ResponseGracefully() {
        Test.setMock(HttpCalloutMock.class, new ErrorMock());

        Test.startTest();
        FutureKawaAPIService.syncAll();
        Test.stopTest();

        System.assertEquals(0, [SELECT COUNT() FROM Coffee_Lot__c]);
        System.assertEquals(0, [SELECT COUNT() FROM Storage_Alert__c]);
    }

    @isTest
    static void testSyncLotsCoversAllThreeCountries() {
        Test.setMock(HttpCalloutMock.class, new LotsAndAlertsMock());

        Test.startTest();
        FutureKawaAPIService.syncLots();
        Test.stopTest();

        Set<String> countries = new Set<String>();
        for (Coffee_Lot__c lot : [SELECT Country__c FROM Coffee_Lot__c]) {
            countries.add(lot.Country__c);
        }

        System.assert(countries.contains('Brésil'));
        System.assert(countries.contains('Équateur'));
    }
}
