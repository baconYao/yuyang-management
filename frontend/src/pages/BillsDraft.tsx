import BillsPageContent from '../components/BillsPageContent';

export default function BillsDraft() {
  return (
    <BillsPageContent
      statusFilter="DRAFT"
      title="未處理的帳單"
    />
  );
}
