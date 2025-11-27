import random
import matplotlib.pyplot as plt
import numpy as np
import hashlib
import uuid

# --- КОНФІГУРАЦІЯ СИМУЛЯЦІЇ ---
NUM_USERS = 200  # Кількість працівників
SIMULATION_HOURS = 24  # Тривалість зміни
ATTACK_START = 10  # Початок DDoS (втрата зв'язку)
ATTACK_END = 15  # Кінець DDoS (відновлення)
SYNC_BATCH_SIZE = 50  # Розмір пакету синхронізації
REQ_PROBABILITY = 0.4  # Активність працівників


# --- ІМІТАЦІЯ КРИПТОГРАФІЇ ТА СТРУКТУР ДАНИХ ---

def calculate_hash(data):
    """Імітація SHA-256"""
    return hashlib.sha256(data.encode()).hexdigest()[:12]


class TransactionRecord:
    """Структура даних транзакції"""

    def __init__(self, user_id, prev_hash):
        self.tx_id = str(uuid.uuid4())
        self.user_id = user_id
        self.prev_hash = prev_hash  # Hash Chaining
        # Імітуємо підпис даних поточним хешем
        self.current_hash = calculate_hash(f"{user_id}{prev_hash}{self.tx_id}")
        self.is_synced = False


class SmartVendingMachine:
    def __init__(self):
        self.state = "ONLINE"  # ONLINE, DEGRADED, OFFLINE
        self.pending_sync = []  # Queue<TransactionRecord>
        self.last_chain_hash = "00000000"  # Initial Vector
        self.total_dispensed = 0
        self.offline_limit_map = {}  # Для контролю аварійної квоти

    def heartbeat(self, is_network_available):
        """Етап 1: Перевірка стану каналу"""
        if is_network_available:
            self.state = "ONLINE"
            # Якщо є накопичені дані - запускаємо синхронізацію
            if len(self.pending_sync) > 0:
                self.perform_batch_sync()
        else:
            self.state = "OFFLINE"  # Trigger Emergency Mode

    def attempt_dispense(self, user_id):
        """Етап 2: Обробка запиту"""

        # Сценарій 1: МЕРЕЖА Є
        if self.state == "ONLINE":
            self.total_dispensed += 1
            return True  # Успішна онлайн видача

        # Сценарій 2: ОФЛАЙН (Аварійний режим)
        else:
            # Перевірка Аварійної Квоти (1 шт на руки в офлайні)
            if self.offline_limit_map.get(user_id, 0) >= 1:
                return False  # Ліміт вичерпано

            # Створення офлайн-транзакції з Hash Chaining
            # --- ВИПРАВЛЕНО ТУТ ---
            tx = TransactionRecord(user_id, prev_hash=self.last_chain_hash)
            # ----------------------

            self.last_chain_hash = tx.current_hash  # Оновлюємо ланцюжок

            # Збереження в локальну чергу
            self.pending_sync.append(tx)
            self.offline_limit_map[user_id] = self.offline_limit_map.get(user_id, 0) + 1
            self.total_dispensed += 1
            return True

    def perform_batch_sync(self):
        """Процедура: Пакетна синхронізація"""
        # Беремо пакет (Batch) транзакцій
        batch_count = 0
        to_remove = []

        for tx in self.pending_sync:
            if batch_count >= SYNC_BATCH_SIZE:
                break
            # Імітація відправки на сервер
            tx.is_synced = True
            to_remove.append(tx)
            batch_count += 1

        # Видалення синхронізованих з черги
        for tx in to_remove:
            self.pending_sync.remove(tx)


# --- ЗАПУСК ЕКСПЕРИМЕНТУ ---

device = SmartVendingMachine()
classic_device_dispensed = 0  # Для порівняння зі старою системою

# Масиви даних для графіків
time_axis = []
queue_size_history = []  # Розмір локальної черги (Pending Sync)
dispensed_proposed = []
dispensed_classic = []

print("Запуск симуляції 'Secure Fail-Safe Protocol'...")

for hour in range(SIMULATION_HOURS):
    # Визначення стану мережі (Атака з 10 до 15 години)
    network_online = not (ATTACK_START <= hour < ATTACK_END)

    # 1. Heartbeat & Sync Cycle
    # В реальності це фоновий процес, тут імітуємо раз на годину
    # (Для наочності пакетного вивантаження робимо кілька циклів синхронізації на годину)
    for _ in range(2):
        device.heartbeat(network_online)

    # 2. Активність користувачів
    for user in range(NUM_USERS):
        if random.random() < REQ_PROBABILITY:
            # Класична система (падає без мережі)
            if network_online:
                classic_device_dispensed += 1

            # Ваша система (працює завжди)
            device.attempt_dispense(f"user_{user}")

    # 3. Збір метрик
    time_axis.append(hour)
    queue_size_history.append(len(device.pending_sync))
    dispensed_proposed.append(device.total_dispensed)
    dispensed_classic.append(classic_device_dispensed)

    status = "🔴 DDoS" if not network_online else "🟢 ONLINE"
    print(f"Hour {hour:02d} | {status} | Queue: {len(device.pending_sync)} tx | Dispensed: {device.total_dispensed}")

# --- ВІЗУАЛІЗАЦІЯ РЕЗУЛЬТАТІВ ---

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# Графік 1: Ефективність бізнес-процесу
ax1.plot(time_axis, dispensed_classic, 'gray', linestyle='--', label='Classic IIoT (No Offline Mode)')
ax1.plot(time_axis, dispensed_proposed, 'green', linewidth=2, label='Proposed Secure Fail-Safe Algo')
ax1.axvspan(ATTACK_START, ATTACK_END, color='red', alpha=0.1, label='DDoS Attack Period')
ax1.set_title('Business Continuity: PPE Dispensing Process')
ax1.set_ylabel('Total Items Dispensed')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Графік 2: Робота алгоритму (Черга та Синхронізація)
ax2.plot(time_axis, queue_size_history, 'blue', marker='o', label='Local Storage Queue (Pending Sync)')
ax2.axvspan(ATTACK_START, ATTACK_END, color='red', alpha=0.1)
ax2.axvspan(ATTACK_END, ATTACK_END + 3, color='green', alpha=0.1, label='Recovery Phase (Batch Sync)')
ax2.text(ATTACK_START + 0.5, max(queue_size_history) / 2, 'Accumulating\nHash Chain', color='blue')
ax2.text(ATTACK_END + 0.5, max(queue_size_history) / 2, 'Batch Upload\n(Packet Size=50)', color='green')
ax2.set_title('Algorithm Performance: Local Storage & Synchronization')
ax2.set_xlabel('Time (Hours)')
ax2.set_ylabel('Transactions in Local Queue')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('algorithm_simulation.png', dpi=300)
plt.show()
