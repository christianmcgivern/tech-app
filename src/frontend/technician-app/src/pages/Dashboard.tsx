import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  Divider,
} from '@mui/material';
import {
  Work as WorkIcon,
  DirectionsCar as TravelIcon,
  Timer as ClockIcon,
  Inventory as InventoryIcon,
  Mic as MicIcon,
} from '@mui/icons-material';
import { useTechnicianStore } from '../store/technicianStore';
import { api } from '../services/api';
import { voiceAgent } from '../services/voiceAgent';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { technicianId } = useTechnicianStore();
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [technicianName, setTechnicianName] = useState<string | null>(null);

  useEffect(() => {
    const fetchTechnicianName = async () => {
      if (technicianId) {
        try {
          const profile = await api.getTechnicianProfile(technicianId);
          setTechnicianName(profile.name);
        } catch (error) {
          console.error('Error fetching technician profile:', error);
        }
      }
    };
    fetchTechnicianName();

    return () => {
      if (voiceAgent.isConnected()) {
        voiceAgent.disconnect();
      }
    };
  }, [technicianId]);

  const handleVoiceAgent = async () => {
    if (isVoiceActive) {
      voiceAgent.disconnect();
      setIsVoiceActive(false);
    } else {
      try {
        if (!technicianId || !technicianName) {
          console.error('Missing technician information');
          return;
        }
        voiceAgent.setTechnicianInfo(technicianId, technicianName);
        await voiceAgent.connect();
        setIsVoiceActive(true);
      } catch (error) {
        console.error('Error connecting to voice agent:', error);
      }
    }
  };

  const handleClockOut = async () => {
    try {
      await api.clockOut(technicianId!);
      // Redirect to login after clock out
      navigate('/');
    } catch (error) {
      console.error('Error clocking out:', error);
    }
  };

  const handleWorkOrders = () => {
    navigate('/work-orders');
  };

  const handleTravel = () => {
    navigate('/travel');
  };

  const handleInventory = () => {
    navigate('/inventory');
  };

  const handleReportIssue = () => {
    navigate('/report-issue');
  };

  const handleContactOffice = () => {
    navigate('/contact-office');
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Voice Agent Button */}
      <Button
        variant="contained"
        color={isVoiceActive ? "secondary" : "primary"}
        fullWidth
        onClick={handleVoiceAgent}
        startIcon={<MicIcon />}
        sx={{ 
          mb: 3, 
          py: 1.5,
          fontSize: '1.1rem',
          backgroundColor: isVoiceActive ? '#f50057' : '#2196f3',
          '&:hover': {
            backgroundColor: isVoiceActive ? '#c51162' : '#1976d2'
          }
        }}
      >
        {isVoiceActive ? 'Stop Voice Agent' : 'Start Voice Agent'}
      </Button>

      <Typography variant="h5" gutterBottom>
        Technician Actions
      </Typography>

      <Grid container spacing={2}>
        {/* Work Orders */}
        <Grid item xs={12} sm={6}>
          <Card>
            <CardContent sx={{ textAlign: 'center', cursor: 'pointer' }} onClick={handleWorkOrders}>
              <WorkIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6">Work Orders</Typography>
              <Typography variant="body2" color="text.secondary">
                View and manage work orders
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Travel Log */}
        <Grid item xs={12} sm={6}>
          <Card>
            <CardContent sx={{ textAlign: 'center', cursor: 'pointer' }} onClick={handleTravel}>
              <TravelIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6">Travel</Typography>
              <Typography variant="body2" color="text.secondary">
                Log travel time and location
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Inventory */}
        <Grid item xs={12} sm={6}>
          <Card>
            <CardContent sx={{ textAlign: 'center', cursor: 'pointer' }} onClick={handleInventory}>
              <InventoryIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6">Inventory</Typography>
              <Typography variant="body2" color="text.secondary">
                Check truck inventory
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Clock Out */}
        <Grid item xs={12} sm={6}>
          <Card>
            <CardContent sx={{ textAlign: 'center', cursor: 'pointer' }} onClick={handleClockOut}>
              <ClockIcon sx={{ fontSize: 40, color: 'error.main', mb: 1 }} />
              <Typography variant="h6">Clock Out</Typography>
              <Typography variant="body2" color="text.secondary">
                End your work day
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 