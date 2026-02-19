import BillsPageContent from '../components/BillsPageContent';

export default function BillsProcessed() {
  return (
    <BillsPageContent
      statusFilter={['PAID', 'OVERDUE', 'CANCELLED']}
      title="已處理的帳單"
    />
  );
}
