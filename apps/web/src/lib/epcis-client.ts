export type EPCISEventType =
  | "pickup"
  | "loaded"
  | "arrived"
  | "delivered"
  | "exception";

export interface SensorReading {
  type: string;
  value: string | number;
  unit?: string;
}

export interface ShipmentEvent {
  type: EPCISEventType;
  sscc: string;
  timestamp: string;
  sensors?: SensorReading[];
}

export class EPCISClient {
  constructor(private baseUrl = "/api/epcis") {}

  async getShipmentEvents(sscc: string): Promise<ShipmentEvent[]> {
    const url = `${this.baseUrl}/shipments/${encodeURIComponent(sscc)}/events`;
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed to fetch events for SSCC ${sscc}`);
    }
    return res.json();
  }
}

export const epcisClient = new EPCISClient();
export default epcisClient;
