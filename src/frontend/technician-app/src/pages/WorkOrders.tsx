import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  AppBar,
  Toolbar,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, Note as NoteIcon } from '@mui/icons-material';
import { useTechnicianStore } from '../store/technicianStore';
import { api } from '../services/api';

interface Note {
  id: number;
  note: string;
  technician_name: string;
  created_at: string;
  alert_office: boolean;
  is_read: boolean;
}

interface WorkOrder {
  id: number;
  title: string;
  status: string;
  scheduled_for: string;
  brief_description: string;
  notes?: Note[];
  notes_count?: number;
  technician_name?: string;
  customer_name?: string;
}

const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      const [datePart, timePart] = dateString.split(' ');
      const [month, day, year] = datePart.split('/');
      const newDate = new Date(`${year}-${month}-${day}${timePart ? ' ' + timePart : ''}`);
      if (!isNaN(newDate.getTime())) {
        return newDate.toLocaleString();
      }
      return dateString;
    }
    return date.toLocaleString();
  } catch (error) {
    console.error('Error formatting date:', error);
    return dateString;
  }
};

const WorkOrders: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { technicianId } = useTechnicianStore();
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkOrders = async () => {
    try {
      if (!technicianId) {
        navigate('/');
        return;
      }
      setLoading(true);
      setError(null);
      const data = await api.getTechnicianWorkOrders(technicianId);
      setWorkOrders(data);
    } catch (error) {
      console.error('Error fetching work orders:', error);
      setError('Failed to load work orders. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkOrders();
  }, [technicianId, navigate, location.key]); // location.key will change when navigating back

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const handleAddNotes = (order: WorkOrder) => {
    navigate(`/work-orders/${order.id}/notes`, { 
      state: { 
        workOrder: {
          id: order.id,
          title: order.title,
          status: order.status,
          scheduled_for: order.scheduled_for,
          brief_description: order.brief_description,
          technician_name: order.technician_name,
          customer_name: order.customer_name
        }
      }
    });
  };

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate('/dashboard')}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6">
            Today's Work Orders
          </Typography>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 2 }}>
        {loading ? (
          <Typography>Loading work orders...</Typography>
        ) : error ? (
          <Box sx={{ textAlign: 'center' }}>
            <Typography color="error" gutterBottom>
              {error}
            </Typography>
            <Button variant="outlined" onClick={fetchWorkOrders}>
              Retry
            </Button>
          </Box>
        ) : workOrders.length === 0 ? (
          <Typography>No work orders assigned for today</Typography>
        ) : (
          <List>
            {workOrders.map((order) => (
              <ListItem
                key={order.id}
                divider
                sx={{ 
                  flexDirection: 'column', 
                  alignItems: 'stretch',
                  p: 2,  // More padding for touch targets
                  backgroundColor: 'white',
                  mb: 1,  // Margin between cards
                  borderRadius: 1,
                  boxShadow: 1
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Typography component="span" variant="subtitle1" sx={{ fontWeight: 'bold', flex: 1 }}>
                    {order.title}
                  </Typography>
                  <Chip
                    label={order.status}
                    color={getStatusColor(order.status) as any}
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Box>
                
                <Typography component="div" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {order.brief_description}
                </Typography>
                
                <Typography component="div" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Scheduled: {order.scheduled_for ? formatDate(order.scheduled_for) : 'Not scheduled'}
                </Typography>

                {(order.notes_count ?? 0) > 0 && (
                  <Box 
                    sx={{ 
                      display: 'flex', 
                      alignItems: 'center',
                      mb: 1,
                      color: 'text.secondary',
                      cursor: 'pointer'
                    }}
                    onClick={() => handleAddNotes(order)}
                  >
                    <NoteIcon fontSize="small" sx={{ mr: 0.5 }} />
                    <Typography component="span" variant="body2">
                      {`${order.notes_count} note${order.notes_count === 1 ? '' : 's'}`}
                    </Typography>
                  </Box>
                )}

                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => handleAddNotes(order)}
                    startIcon={<NoteIcon />}
                    sx={{ 
                      width: '100%',  // Full width on mobile
                      borderRadius: 4,  // Rounded corners
                      textTransform: 'none'  // No uppercase
                    }}
                  >
                    {(order.notes_count ?? 0) > 0 ? 'View/Add Notes' : 'Add Notes'}
                  </Button>
                </Box>
              </ListItem>
            ))}
          </List>
        )}
      </Box>
    </Box>
  );
};

export default WorkOrders; 