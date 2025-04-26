export interface ChargeRecordResponse {
  rtnCode: number;
  msg: string;
  ts: number;
  bizData: {
    chartList: {
      timestampStop: string;
      energy: number;
    }[];
    dataList: {
      email: string;
      timestampStart: number;
      timestampStop: number;
      duration: string;
      energy: string;
      cost: string;
      costNoUnit: string | null;
      currency: string | null;
    }[];
  };
}
