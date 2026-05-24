db = db.getSiblingDB("taximongo");

db.createCollection("users");
db.createCollection("drivers");
db.createCollection("trips", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "client", "status", "route", "created_at"],
      properties: {
        user_id: { bsonType: "objectId" },
        driver_id: { bsonType: ["objectId", "null"] },
        client: {
          bsonType: "object",
          required: ["login", "first_name", "last_name"],
          properties: {
            login: { bsonType: "string", minLength: 1, maxLength: 64 },
            first_name: { bsonType: "string", minLength: 1 },
            last_name: { bsonType: "string", minLength: 1 },
          },
        },
        status: { enum: ["pending", "active", "completed"] },
        route: {
          bsonType: "object",
          required: ["from", "to"],
          properties: {
            from: { bsonType: "string", minLength: 1 },
            to: { bsonType: "string", minLength: 1 },
          },
        },
        tags: { bsonType: "array", items: { bsonType: "string" } },
        events: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["at", "type"],
            properties: {
              at: { bsonType: "date" },
              type: { bsonType: "string" },
            },
          },
        },
        created_at: { bsonType: "date" },
      },
    },
  },
  validationLevel: "strict",
  validationAction: "error",
});

db.users.createIndex({ login: 1 }, { unique: true });
db.drivers.createIndex({ user_id: 1 }, { unique: true });
db.trips.createIndex({ status: 1, created_at: -1 });
db.trips.createIndex({ user_id: 1, status: 1 });

try {
  db.trips.insertOne({ user_id: new ObjectId(), status: "pending", created_at: new Date() });
  print("ERROR: invalid doc inserted");
} catch (e) {
  print("invalid insert rejected:", e.codeName);
}
