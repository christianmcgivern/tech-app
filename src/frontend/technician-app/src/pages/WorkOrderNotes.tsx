import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  IconButton,
  AppBar,
  Toolbar,
  List,
  ListItem,
  TextField,
  Button,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, Note as NoteIcon } from '@mui/icons-material';
import { api } from '../services/api';
import { useTechnicianStore } from '../store/technicianStore';

interface Note {
  id: number;
  note_text: string;
  technician_name: string;
  created_at: string;
  alert_office: boolean;
}

interface WorkOrder {
  id: number;
  title: string;
  brief_description: string;
  notes: Note[];
}

const WorkOrderNotes: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { technicianId } = useTechnicianStore();
  const [notes, setNotes] = useState<Note[]>([]);
  const [newNote, setNewNote] = useState('');
  const [alertOffice, setAlertOffice] = useState(false);
  const [loading, setLoading] = useState(false);
  const workOrder = location.state?.workOrder;

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const fetchNotes = async () => {
    if (!orderId) return;
    try {
      const response = await api.getWorkOrder(Number(orderId));
      if (response.notes) {
        setNotes(response.notes);
      }
    } catch (error) {
      console.error('Error fetching notes:', error);
    }
  };

  useEffect(() => {
    fetchNotes();
  }, [orderId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim() || !orderId || !technicianId) return;

    setLoading(true);
    try {
      await api.updateWorkOrderNotes(Number(orderId), {
        notes: newNote,
        technician_id: technicianId,
        alert_office: alertOffice,
      });
      setNewNote('');
      setAlertOffice(false);
      await fetchNotes();
    } catch (error) {
      console.error('Error saving note:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate(-1)}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" component="div">
              {workOrder?.title || 'Work Order Notes'}
            </Typography>
            <Typography variant="subtitle2" component="div">
              {workOrder?.brief_description}
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <List>
          {notes.map((note) => (
            <ListItem
              key={note.id}
              sx={{
                flexDirection: 'column',
                alignItems: 'flex-start',
                backgroundColor: 'white',
                borderRadius: 1,
                mb: 1,
                p: 2,
                boxShadow: 1,
              }}
            >
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 1, width: '100%' }}>
                {note.note_text}
              </Typography>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  width: '100%',
                  mt: 1,
                  color: 'text.secondary',
                }}
              >
                <Typography variant="caption">
                  By {note.technician_name}
                </Typography>
                <Typography variant="caption">
                  {formatDate(note.created_at)}
                </Typography>
              </Box>
              {note.alert_office && (
                <Typography
                  variant="caption"
                  sx={{ color: 'warning.main', mt: 1 }}
                >
                  Office alerted
                </Typography>
              )}
            </ListItem>
          ))}
        </List>
      </Box>

      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: 2,
          backgroundColor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <TextField
          fullWidth
          multiline
          rows={3}
          value={newNote}
          onChange={(e) => setNewNote(e.target.value)}
          placeholder="Add a note..."
          variant="outlined"
          sx={{ mb: 2 }}
        />
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <FormControlLabel
            control={
              <Switch
                checked={alertOffice}
                onChange={(e) => setAlertOffice(e.target.checked)}
                color="warning"
              />
            }
            label="Alert office"
          />
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !newNote.trim()}
            sx={{ borderRadius: 4 }}
          >
            Add Note
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default WorkOrderNotes; 