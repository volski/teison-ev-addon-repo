export interface ChargerConfigModel{
  id: number;
  cpId: number;
  createTime: number; // Unix timestamp in milliseconds
  updateTime: number; // Unix timestamp in milliseconds
  directWorkMode: boolean;
  directlyScheduleConstraintInfo: number;
  ledStrength: number;
  maxCurrent: number;
  maxRandomDelay: number;
  stopTranOnEVSideDiscon: boolean;
  timezone: string;
}