import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  IconButton,
  AppBar,
  Toolbar,
  Button,
  Card,
  CardContent,
  TextField,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  LocationOn as LocationIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';

const Travel: React.FC = () => {
  const navigate = useNavigate();
  const [isTracking, setIsTracking] = useState(false);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [notes, setNotes] = useState('');

  const handleStartTravel = () => {
    setIsTracking(true);
    setStartTime(new Date());
  };

  const handleEndTravel = () => {
    // TODO: Implement API call to save travel record
    setIsTracking(false);
    setStartTime(null);
    setNotes('');
    navigate('/dashboard');
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
            Travel Tracking
          </Typography>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 2 }}>
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <LocationIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">
                Location Tracking
              </Typography>
            </Box>
            {isTracking ? (
              <>
                <Typography color="primary" gutterBottom>
                  Currently tracking your travel
                </Typography>
                {startTime && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <TimerIcon sx={{ mr: 1 }} />
                    <Typography>
                      Started at: {startTime.toLocaleTimeString()}
                    </Typography>
                  </Box>
                )}
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  variant="outlined"
                  label="Travel Notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  sx={{ mb: 2 }}
                />
                <Button
                  variant="contained"
                  color="secondary"
                  fullWidth
                  onClick={handleEndTravel}
                >
                  End Travel
                </Button>
              </>
            ) : (
              <Button
                variant="contained"
                color="primary"
                fullWidth
                onClick={handleStartTravel}
              >
                Start Travel
              </Button>
            )}
          </CardContent>
        </Card>

        <Typography variant="body2" color="text.secondary" align="center">
          Your location will be tracked while traveling to help maintain accurate records.
        </Typography>
      </Box>
    </Box>
  );
};

export default Travel; 