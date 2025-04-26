import forge from "node-forge";

export function getDeviceStatus(status: number): string {
  if (status == 88) {
    return "Faulted";
  }
  switch (status) {
    case 0:
      return "Available";
    case 1:
      return "Preparing";
    case 2:
      return "Charging";
    case 3:
      return "SuspendedEVSE";
    case 4:
      return "SuspendedEV";
    case 5:
      return "Finished";
    case 6:
      return "Reserved";
    case 7:
      return "Unavailable";
    case 8:
      return "Faulted";
    default:
      return "";
  }
}
  export function getDeviceStatusColor(status: number): string {
    if (status == 88) {
      return "red";
    }
    switch (status) {
      case 0:
        return "green";
      case 1:
        return "orange";
      case 2:
        return "orange";
      case 3:
        return "red";
      case 4:
        return "red";
      case 5:
        return "red";
      case 6:
        return "red";
      case 7:
        return "red";
      case 8:
        return "red";
      default:
        return "red";
    }
  }
