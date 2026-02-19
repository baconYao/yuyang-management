import BillsPageContent from '../components/BillsPageContent';

export default function BillsProcessing() {
  return (
    <BillsPageContent
      statusFilter={['SENT', 'PROCESSING']}
      title="請款中的帳單"
    />
  );
}
