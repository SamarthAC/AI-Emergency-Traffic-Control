import { FiList } from "react-icons/fi";
import Card from "../common/Card";

const ITEMS: { label: string; color: string }[] = [
  { label: "Car", color: "#5B8DEF" },
  { label: "Bike", color: "#B084F0" },
  { label: "Bus", color: "#F2C14E" },
  { label: "Truck", color: "#8B9AAE" },
  { label: "Ambulance", color: "#F4F6F8" },
];

export default function Legend() {
  return (
    <Card title="Legend" icon={<FiList />}>
      <div className="grid grid-cols-2 gap-y-2 gap-x-3">
        {ITEMS.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: item.color }} />
            <span className="text-xs text-muted">{item.label}</span>
          </div>
        ))}
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-signal-green shrink-0" />
          <span className="text-xs text-muted">Traffic Signal</span>
        </div>
      </div>
    </Card>
  );
}
