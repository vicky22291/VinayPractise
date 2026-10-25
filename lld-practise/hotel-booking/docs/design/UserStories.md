# User Stories

`UserStoriesFunctionalTest` chains the APIs the way an owner and guests use them. After each step it checks that the APIs agree with each other. The per-API tests check each API on its own, and these check that they work together.

Shared test rules: [Overview.md](Overview.md#tests). Today is 2026-10-24. Each story creates one hotel in a city of its own. Every booking is for 1 room, and "search" means a search of that city for the stay named.

| Story | Steps | Expect |
|---|---|---|
| `guestsBookUntilSoldOut` | Deluxe has 2 rooms. Three guests each book Nov 10–12, with a search before each booking. Then search without dates, and get the hotel | the searches show 2, 1, then no hotel; the third booking gets 409 `ROOMS_NOT_AVAILABLE`; without dates the hotel is still listed; `count` is still 2 |
| `backToBackStaysShareCheckoutDate` | Deluxe has 1 room. Guest 1 books Nov 10–12. Search Nov 11–13 and Nov 12–14. Guest 2 books Nov 12–14, and guest 3 books Nov 11–12 | Nov 11–13 shows no hotel and Nov 12–14 shows 1; guest 2 gets 201 and guest 3 gets 409 |
| `ownerAddsRoomsToSoldOutRoomType` | Deluxe has 1 room, booked for Nov 10–12. The owner raises `count` to 2, a second guest books, then the owner tries `count` 1 | after the raise, search shows 1 and the second booking gets 201; `count` 1 gets 409 `ROOM_COUNT_BELOW_RESERVED`, and get still shows 2 |
| `ownerAddsRoomTypeToSoldOutHotel` | Deluxe has 1 room, booked for Nov 10–12. The owner adds a Suite, and a guest books it | search shows only the Suite, with 1; the booking gets 201 at the Suite's price; then search shows no hotel |
| `searchAndBookingFollowHotelEdits` | Deluxe has 2 rooms at 4500.00, and a guest books Nov 10–12. One update moves the hotel to another city and sets the price to 5000.00. A second guest books | the old city shows no hotel, and the new one shows Deluxe with 1; the first booking stays at 4500.00 a night, and the second costs 5000.00 |
