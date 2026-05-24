db = db.getSiblingDB("taximongo");

const uid = (n) => ObjectId(`674a100000000000000000${String(n).padStart(2, "0")}`);
const did = (n) => ObjectId(`674a200000000000000000${String(n).padStart(2, "0")}`);
const tid = (n) => ObjectId(`674a300000000000000000${String(n).padStart(2, "0")}`);

db.users.deleteMany({});
db.drivers.deleteMany({});
db.trips.deleteMany({});

const clients = [
  ["client1", "Иван", "Петров"],
  ["client2", "Мария", "Сидорова"],
  ["client3", "Пётр", "Козлов"],
  ["client4", "Ольга", "Новикова"],
  ["client5", "Сергей", "Морозов"],
];

const driverLogins = Array.from({ length: 12 }, (_, i) => [
  `driver${i + 1}`,
  ["Алексей", "Дмитрий", "Никита", "Елена", "Игорь", "Павел", "Олег", "Кирилл", "Максим", "Артём", "Роман", "Вадим"][i],
  ["Волков", "Орлов", "Белов", "Громова", "Лебедев", "Соколов", "Кузнецов", "Попов", "Васильев", "Михайлов", "Фёдоров", "Новиков"][i],
]);

const users = [...clients, ...driverLogins].map(([login, first_name, last_name], i) => ({
  _id: uid(i + 1),
  login,
  first_name,
  last_name,
  password_hash: "",
  phones: [`+790000000${String(i).padStart(2, "0")}`],
  roles: login.startsWith("driver") ? ["driver"] : ["passenger"],
  created_at: new Date(`2026-01-${String((i % 28) + 1).padStart(2, "0")}T10:00:00Z`),
}));

db.users.insertMany(users);

const cars = [
  ["Kia Rio", "А111АА777", 2019],
  ["Hyundai Solaris", "В222ВВ777", 2021],
  ["Toyota Camry", "С333СС777", 2020],
  ["Skoda Octavia", "Е444ЕЕ777", 2018],
  ["Volkswagen Polo", "К555КК777", 2022],
  ["Renault Logan", "М666ММ777", 2017],
  ["Lada Vesta", "Н777НН777", 2023],
  ["BMW 3", "О888ОО777", 2019],
  ["Mercedes C", "Р999РР777", 2020],
  ["Audi A4", "Т000ТТ777", 2021],
  ["Geely Coolray", "У111УУ777", 2022],
  ["Chery Tiggo", "Х222ХХ777", 2023],
];

db.drivers.insertMany(
  cars.map(([model, plate, year], i) => ({
    _id: did(i + 1),
    user_id: uid(clients.length + i + 1),
    car: { model, plate, year },
    rating: 4 + (i % 10) / 10,
    registered_at: new Date(`2026-02-${String((i % 28) + 1).padStart(2, "0")}T09:00:00Z`),
  })),
);

const statuses = [
  "completed", "completed", "active", "pending", "pending",
  "completed", "active", "pending", "completed", "active", "pending", "completed",
];

db.trips.insertMany(
  statuses.map((status, i) => {
    const u = users[i % 5];
    const hasDriver = status !== "pending";
    return {
      _id: tid(i + 1),
      user_id: u._id,
      driver_id: hasDriver ? did((i % 12) + 1) : null,
      client: { login: u.login, first_name: u.first_name, last_name: u.last_name },
      status,
      route: { from: `точка A-${i}`, to: `точка B-${i}` },
      tags: i % 2 === 0 ? ["economy"] : ["comfort"],
      events: [{ at: new Date(`2026-03-${String((i % 28) + 1).padStart(2, "0")}T08:00:00Z`), type: "created" }],
      created_at: new Date(`2026-03-${String((i % 28) + 1).padStart(2, "0")}T08:00:00Z`),
    };
  }),
);

print("users:", db.users.countDocuments());
print("drivers:", db.drivers.countDocuments());
print("trips:", db.trips.countDocuments());
