public class FutureKawaSyncScheduler implements Schedulable {

    public void execute(SchedulableContext ctx) {
        FutureKawaAPIService.syncAll();
    }
}
