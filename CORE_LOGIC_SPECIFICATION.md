# Secure Fail-Safe Protocol: Core Logic Specification

## Overview
This document outlines the detailed pseudocode and data structures for the hybrid Edge-Cloud PPE dispensing system.

### 1. Data Structures

```c
STRUCT TransactionRecord {
    String tx_id;              // UUID
    String card_id;            // User ID
    String item_id;            // PPE Item Code
    Timestamp timestamp;       // Unix timestamp
    String device_id;          // Unique Device ID
    Boolean is_offline;        // Offline flag
    String prev_hash;          // Hash Chaining (Previous)
    String current_hash;       // Hash Chaining (Current)
    String signature;          // Digital Signature (Ed25519)
    Integer retry_count;       // Sync retry counter
}

STRUCT DeviceState {
    String connection_status;  // "ONLINE" | "OFFLINE" | "DEGRADED"
    Timestamp last_heartbeat;  
    Integer failed_attempts;   
    String current_mode;       // "NORMAL" | "EMERGENCY"
    Queue<TransactionRecord> pending_sync; 
    String init_vector;        // IV for hash chain
}
2. Main Algorithm (Fail-Safe Logic)
BEGIN MAIN_ALGORITHM
TRY
    // --- STAGE 1: CONNECTION CHECK ---
    Time_Delta := Current_Time - device_state.last_heartbeat

    IF Time_Delta < T_CRIT THEN
        device_state.connection_status := "ONLINE"
    ELSE IF Time_Delta < (T_CRIT * 2) THEN
        device_state.connection_status := "DEGRADED"
    ELSE
        device_state.connection_status := "OFFLINE"
        Trigger_Emergency_Mode()
    END IF

    // --- STAGE 2: REQUEST PROCESSING ---
    IF device_state.connection_status == "ONLINE" THEN
        RETURN Process_Online_Request(Card_ID, Item_ID)

    ELSE IF device_state.connection_status == "DEGRADED" THEN
        TRY
            RETURN Process_Online_Request_With_Timeout(Card_ID, Item_ID, timeout=5)
        CATCH TimeoutException
            RETURN Process_Offline_Request(Card_ID, Item_ID)
        END TRY

    ELSE // OFFLINE MODE
        RETURN Process_Offline_Request(Card_ID, Item_ID)
    END IF

CATCH SecurityException AS e
    Log_Event("ERROR", "Security violation: " + e.message)
    RETURN FALSE
END MAIN_ALGORITHM
3. Offline Processing & Hash Chaining
FUNCTION Process_Offline_Request(Card_ID, Item_ID) RETURNS Boolean
BEGIN
    // 1. Storage Check
    IF device_state.offline_tx_count >= MAX_OFFLINE_TX THEN
        RETURN FALSE 
    END IF

    // 2. Local Cache Validation
    Card_Hash := Calculate_Hash(Card_ID)
    IF Card_Hash NOT IN local_cache THEN
        RETURN FALSE
    END IF

    // 3. Crypto-Validation & Dispensing
    Dispense_Item(Item_ID)
    
    // 4. Create Secure Record (Hash Chain)
    Tx := Create_Offline_Transaction(Card_ID, Item_ID)
    device_state.pending_sync.Enqueue(Tx)
    
    RETURN TRUE
END FUNCTION
