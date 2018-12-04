#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <time.h>

#define MAXLEN 		2048
unsigned int portno = 10001;
char hostname[] = "192.168.0.9";
char button[]="<INPUT TYPE=\"BUTTON\" VALUE=\"%s\" ONCLICK=\"window.location.href='%s'\">";

char wgr[]= "http://i.wund.com/auto/iphone/geo/TouchMap/index.html?lat=39.95780563&lon=-86.27529907";
// "\"http://i.wund.com/cgi-bin/findweather/getForecast?brand=iphone&query=46077#radar\"";

char *chanDesc[3]= {"Attic  ",
                    "Inside ",
                    "Outside"};
unsigned char VariableLengthMode[2]={0xF0,0x2C};
unsigned char EnableAllRF[2]={0xF0,0x2A};

unsigned char AllSensors[3][12];



int 
await_input(int filedes, unsigned int msec)
{
  fd_set rfds;
  struct timeval tv;
  int retval;
  time_t rawtime;
  struct tm * timeinfo;
  char ts[80]; 

  /* Watch stdin (fd 0) to see when it has input. */
  FD_ZERO(&rfds);
  FD_SET(filedes, &rfds);
 
  tv.tv_sec = 0;
  tv.tv_usec = msec*1000;

//  printf("sock=%d\n",filedes);
  retval = select(filedes+1, &rfds, NULL, NULL, &tv);
  
   if (retval == -1)
        perror("select()");
   else if (retval)
     return 0;
        /* printf("Data is available now.\n"); */
        /* FD_ISSET(0, &rfds) will be true. */
   else
  {
     time ( &rawtime );
     timeinfo = localtime ( &rawtime );
     strftime (ts,80,"%Y%m%d%H%M%S ",timeinfo);
     printf("%s No data within timeout period.\n", ts);
  }
  return 0;
}

int
read_ack (int filedes)
{
  struct timeval tv;

  int nbytes;
  int readLen;
  int i;
  time_t rawtime;
  struct tm * timeinfo;
  char ts[80]; 
  unsigned char b;
  time ( &rawtime );
  timeinfo = localtime ( &rawtime );

  /* time stamp */
  strftime (ts,80,"%Y%m%d%H%M%S ",timeinfo);
  printf ("%s ", ts);

 /* read length */
  nbytes = read (filedes, &b, 1);
  if (nbytes < 0)
    {
      /* Read error.  */
      perror ("read");
      exit (EXIT_FAILURE);
    }
  else if (nbytes == 0)
    /* End-of-file.  */
    printf ("eof");
  else
    {
      for (i=0; i<nbytes; i++)
        printf ("%02x ", b);
    }

    printf ("\n");
}

int
readPacket (int filedes, unsigned char *b)
{
  struct timeval tv;
  int nbytes;
  int i;

 /* read length */
  nbytes = read (filedes, b, 1);
  if (nbytes < 0)
    {
      /* Read error.  */
      perror ("read");
      exit (EXIT_FAILURE);
    }
  else if (nbytes == 0)
    /* End-of-file.  */
    return -1;
  else
    {
    }

  await_input(filedes, 50); /* wait UPTO 30ms */

  /* read in packet content, all Oregon Scientific packets are 10 bytes long */
  nbytes = read (filedes, &b[1], MAXLEN);
  if (nbytes < 0)
  {
      /* Read error.  */
      perror ("read");
      exit (EXIT_FAILURE);
  }
  else if (nbytes == 0)
    /* End-of-file.  */
    return -1;
  else
  {
      return 10; 
  }
}

void decodePacket(char *buf,unsigned int *channel,double *tc,double *tf,double *hum,unsigned int *address,unsigned int *hs,unsigned int *bs)
{
  int i;
  double t1,t2,t3;
  double h1,h2;
  unsigned char *b= &buf[1];
  unsigned char pl;

  /* clear data */
  *channel= 0xFFF;
  *tc= 0;
  *tf= 0.0;
  *hum= 0.0;
  *address=0x0;
  *hs= 0;
  *bs= 0;

  pl= buf[0]&0x7f;
  pl >>= 3; 

  if (b[0]==0x1A && b[1]==0x2D)
  {
    /* channel */
    if ((b[2]&0x10)) *channel= 1;
    if ((b[2]&0x20)) *channel= 2;
    if ((b[2]&0x40)) *channel= 3;

    /* address */
    *address= b[3];

    /* temperature */
    t1= (double)(b[5]>>4);
    t2= (double)(b[5]&0x0F); 
    t3= (double)(b[4]>>4);

    /* absolute temperature in celsius */
    *tc= t1*10.0+t2+t3/10.0;

    /* negative temperature? */
    if (b[6]&0x08) *tc = -(*tc);

    /* f */
    *tf = (9.0/5.0)*(*tc)+32.0;
   
    /* humidity */ 
    h1= (double)(b[7]&0x0F); 
    h2= (double)(b[6]>>4);
    *hum= h1*10.0+h2;
      
    /* humidity status */
    *hs= (b[7]>>6);

    /* batt status 0 ok 1 low */ 
    *bs= (b[4]&0x04);
  }
}

void printPacket(int readLen, unsigned char *buf)
{
  int i;
  double t1,t2,t3,tf,tc;
  double h1,h2,hum;
  unsigned int channel, address,hs;
  unsigned char *b= &buf[1];
  unsigned char pl;

  pl= buf[0]&0x7f;
  pl >>= 3; 
  printf ("Len: P%d A%d ", pl, readLen);
  for (i=0; i<readLen+1; i++)
    printf ("%02x ", buf[i]);
  printf ("\n");

  if (b[0]==0x1A && b[1]==0x2D)
  {
    /* channel */
    if ((b[2]&0x10)) channel= 1;
    if ((b[2]&0x20)) channel= 2;
    if ((b[2]&0x40)) channel= 3;

    /* address */
    address= b[3];

    /* temperature */
    t1= (double)(b[5]>>4);
    t2= (double)(b[5]&0x0F); 
    t3= (double)(b[4]>>4);

    /* absolute temperature in celsius */
    tc= t1*10.0+t2+t3/10.0;

    /* negative temperature? */
    if (b[6]&0x08) tc = -tc;

    tf = (9.0/5.0)*tc+32.0;
    printf("C:%d (%s) ADDR:%02x Temp:%4.1lff/%4.1lfc",channel,chanDesc[channel-1],address,tf,tc);
   
    /* humidity */ 
    h1= (double)(b[7]&0x0F); 
    h2= (double)(b[6]>>4);
    hum= h1*10.0+h2;
    printf(" humidity %2.0lf\%",hum);
      
    /* humidity status */
    hs= (b[7]>>6);
    switch (hs)
    {
      case 0: printf(" NORM "); break; 
      case 1: printf(" COMF "); break; 
      case 2: printf(" *DRY "); break; 
      case 3: printf(" *WET "); break; 
    }

    /* batt status 0 ok 1 low */ 
    printf(" batt %s",(b[4]&0x04)?"LOW":"OK");
    printf("\n");
  }
}

int 
validatePacket(int readLen, unsigned char *buf)
{
  unsigned char *b= &buf[1];
  unsigned char pl;
  unsigned int sum;
  int i;

  /* check received length */
  if (readLen!=10)
    return 1;

  /* check length byte inside packet */
  pl= buf[0]&0x7f;
  pl >>= 3; 
  if (pl!=10)
    return 2;

  /* oregon scientific sensor we have? */
  if (b[0]!=0x1A && b[1]!=0x2D)
    return 3;

  /* examine checksum 1- 8 bits checksum. addition of all nibbles minus 0x0A */ 
  sum= 0;
  for (i= 0; i<8; i++)
    sum += (b[i]&0x0f)+(b[i]>>4);
  sum -= 0x0A;
//  printf("Checksum 1: %02x==%02x? ", sum, b[8]);
  if (sum!=b[8])
    return 4;

  return 0;
}

void 
write_to_server (int filedes, char *s, int len)
{
  int nbytes;

  nbytes = write (filedes, s, len);
  if (nbytes < 0)
    {
      perror ("write");
      exit (EXIT_FAILURE);
    }
}

static char lastWrite[80];

void logPacket(unsigned int channel, double tc, double tf, double hum, unsigned int address, unsigned int hs, unsigned int bs)
{
  FILE *fp;
  time_t rawtime;
  struct tm * timeinfo;
  char ts[80];
  char filename[80];
  char filenamePrefix[80];
  char output[80];
  time ( &rawtime );
  timeinfo = localtime ( &rawtime );

  /* time stamp */
  strftime (ts,80,"%Y%m%d%H%M%S",timeinfo);
  strftime (filenamePrefix,80,"%Y%m%d",timeinfo);
  sprintf(filename,"temperature/%s.log",filenamePrefix);
  fp= fopen(filename,"a");

  // log only valid channel info
  if (channel>0 && channel<4)
  {
    sprintf(output,"%s,%u,%4.1lf,%4.1lf,%2.0lf,%u,%u,%u",ts,channel,tc,tf,hum,address,hs,bs);
    
    // skip repeat messages
    // I guess messages are always sent twice to ensure each heart beat is heard
    //
    if (strncmp(&lastWrite[0],&output[0],80))
    {
      strcpy(lastWrite,output);
      fprintf(fp,"%s\n",output);

  /* Humidity status
	case 0: fprintf(fp," NORM "); break; 
        case 1: fprintf(fp," COMF "); break; 
        case 2: fprintf(fp," *DRY "); break; 
        case 3: fprintf(fp," *WET "); break; 
   */
      /* batt status 0 ok 1 low */ 
    }
  }
  fclose(fp);
}

/* note: these are scripts that must go in the header */
void WriteGauges(FILE *fp, int celsius)
{
  int i, rows;
  unsigned int channel, cbf;
  double tc, tf, hum;
  unsigned int address, hs, bs;

  fprintf(fp,"<script type='text/javascript' src='https://www.google.com/jsapi'></script>\n");
  fprintf(fp,"<script type='text/javascript'>\n");
  fprintf(fp,"google.load('visualization', '1', {packages:['gauge']});\n");
  fprintf(fp,"google.setOnLoadCallback(drawInfo);\n");
  fprintf(fp, "function drawInfo() \n");
  fprintf(fp," { \n");

/* data.addColumn('string', 'Label'); */
  fprintf(fp," var tempData = new google.visualization.DataTable(); \n");
  fprintf(fp," tempData.addColumn('number', 'Outside'); \n");
  fprintf(fp," tempData.addColumn('number', 'Attic'); \n");
  fprintf(fp," tempData.addColumn('number', 'Inside'); \n");
  fprintf(fp," tempData.addRows(3); \n");

  fprintf(fp," var humData = new google.visualization.DataTable(); \n");
  fprintf(fp," humData.addColumn('number', 'Outside'); \n"); // 2
  fprintf(fp," humData.addColumn('number', 'Attic'); \n"); // 0
  fprintf(fp," humData.addColumn('number', 'Inside'); \n"); // 1
  fprintf(fp," humData.addRows(3); \n");

  cbf= 0;
  for (i= 0; i<3; i++)
  {
    decodePacket(&AllSensors[i][0],&channel,&tc,&tf,&hum,&address,&hs,&bs);
    if (channel>0 && channel<4)
    {
      cbf |= (1<<(channel-1));
      fprintf(fp,"tempData.setCell(0,%d,%4.1lf); \n", channel%3, celsius?tc:tf);
      fprintf(fp,"humData.setCell(0,%d,%2.0lf); \n", channel%3, hum);
    }
  }
 
  // set remaining
/*  for (i= 0; i<3; i++)
  {
      if ( (cbf&(1<<i))==0)
      {
        fprintf(fp," tempData.setCell(0,%d,%4.1lf); \n", i);
        fprintf(fp," humData.setCell(0,%d,%2.0lf); \n", i);
      }
  }
*/
  fprintf(fp," var temp; \n");
  fprintf(fp," temp = new google.visualization.Gauge(document.getElementById('temp_div')); \n");
  fprintf(fp," var tempOptions = {min: -25, max: 125, yellowFrom: -25, yellowTo: 32, greenFrom:60, greenTo:85, redFrom: 92, redTo: 130, minorTicks: 5}; \n"); /* width: 400, height: 120 */
  fprintf(fp," temp.draw(tempData, tempOptions); \n");

  fprintf(fp," var hum; \n");
  fprintf(fp," hum = new google.visualization.Gauge(document.getElementById('hum_div')); \n");
  fprintf(fp," var humOptions = {min: 0, max: 100, yellowFrom: 0, yellowTo: 35, greenFrom:40, greenTo:55, redFrom: 65, redTo: 100, minorTicks: 5}; \n"); /* width: 400, height: 120 */
  fprintf(fp," hum.draw(humData, humOptions); \n");

  fprintf(fp," } \n");
  fprintf(fp," </script> \n");
}

void WriteHeader(FILE *fp)
{

// apple specific tags
  fprintf(fp,"<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">\n");
  fprintf(fp,"<meta name=\"apple-mobile-web-app-status-bar-style\" content=\"black\">\n");
  fprintf(fp,"<meta name=\"format-detection\" content=\"telephone=no\">\n");
  fprintf(fp,"<meta name = \"viewport\" content = \"width = device-width\">\n");
  fprintf(fp,"<meta name = \"viewport\" content = \"height = device-height\">\n");
  //fprintf(fp,"<meta name=\"viewport\" content=\"width=320; initial-scale=1.0; maximum-scale=1.0; user-scalable=0;\"/>\n");

  fprintf(fp,"<meta http-equiv=\"X-UA-Compatible\" content=\"IE=9; IE=7\">\n");
  fprintf(fp,"<meta http-equiv=\"refresh\" content=\"15\">\n");
  fprintf(fp,"<meta http-equiv=\"CACHE-CONTROL\" CONTENT=\"NO-CACHE\">\n");
  fprintf(fp,"<meta http-equiv=\"EXPIRES\" CONTENT=\"-1\">\n");
  fprintf(fp,"<meta http-equiv=\"pragma\" CONTENT=\"no-cache\">\n");
  WriteGauges(fp, 0);
}


void WriteSensors(int celsius)
{
  unsigned int channel;
  double tc;
  double tf;
  double hum;
  unsigned int address;
  unsigned int hs;
  unsigned int bs;
  FILE *fp;
  int i;
  time_t rawtime;
  struct tm * timeinfo;
  char ts[80];
  char filename[80];
  time ( &rawtime );
  timeinfo = localtime ( &rawtime );

  sprintf(filename,"AllSensors%s.html",celsius?"C":"");
  fp= fopen(filename,"w");

  fprintf(fp,"<html>\n");
  fprintf(fp,"<title>Temperature and Humidity Sensors</title>\n");
  fprintf(fp,"<head>\n");
  WriteHeader(fp);
  fprintf(fp,"</head>\n");
// image to show user if they add this url to their home page as an icon
// <link rel="apple-touch-icon" href="image.png" />
// The home screen PNG image must be 57 by 57 pixels. 
// Apple's software will apply pretty shines to it, so just make
// something simple. 
  fprintf(fp,"<body>\n");
  fprintf(fp,"<form>\n");

  fprintf(fp,"<input type=\"hidden\" id=\"refreshed\" value=\"no\">\n");
  strftime (ts,80,"%Y%m%d",timeinfo);
  fprintf(fp, button, "Radar", wgr);
  fprintf(fp, button, "Sensors", "http://bogyi.dyndns.org/~plastic/cgi-bin/g.cgi");
  fprintf(fp, button, "Overlay", "http://bogyi.dyndns.org/~plastic/cgi-bin/g2.cgi");
  fprintf(fp, button, "C", "AllSensorsC.html");
  fprintf(fp, button, "F", "AllSensors.html");

  fprintf(fp,"<table border=\"0\" style=\"color: blue\" width=\"100\%\">\n");
  fprintf(fp,"<tr>\n");
  fprintf(fp,"<td><u>Loc</u></td>\n");
  fprintf(fp,"<td><u>Temp</u></td>\n");
  fprintf(fp,"<td><u>Hum</u></td>\n");
  fprintf(fp,"<td></td>\n");
  fprintf(fp,"<td><u>Batt</u></td>\n");
  fprintf(fp,"</tr>\n");
  
  for (i= 0; i<3; i++)
  {
    fprintf(fp,"<tr>\n");

    decodePacket(&AllSensors[i][0],&channel,&tc,&tf,&hum,&address,&hs,&bs);
    if (channel>0 && channel<4)
    {
      fprintf(fp,"<td>%s</td>\n",chanDesc[channel-1]);
      fprintf(fp,"<td>%4.1lf%s</td>",celsius?tc:tf,celsius?"c":"f");

      /* humidity status */
      fprintf(fp,"<td>%2.0lf\%</td>",hum);
      fprintf(fp,"<td>\n");
      switch (hs)
      {
	case 0: fprintf(fp," NORM "); break; 
        case 1: fprintf(fp," COMF "); break; 
        case 2: fprintf(fp," *DRY "); break; 
        case 3: fprintf(fp," *WET "); break; 
      }
      fprintf(fp,"</td>\n");

      /* batt status 0 ok 1 low */ 
      fprintf(fp,"<td>%s</td>",bs?"LOW":"OK");
      fprintf(fp,"</tr>\n");
    }
  }

  fprintf(fp,"</table>");

  fprintf(fp,"<b>Temperature</b>\n");
  fprintf(fp,"<div id='temp_div'></div><br>\n");
  fprintf(fp,"<b>Humidity</b>\n");
  fprintf(fp,"<div id='hum_div'></div>\n");

  /* time stamp */
  strftime (ts,80,"%Y-%m-%d %H:%M:%S",timeinfo);
  fprintf(fp,"Last Updated: %s \n", ts);

  fprintf(fp,"</form>\n");
  fprintf(fp,"</body>\n");
  fprintf(fp,"</html>\n");
  fclose(fp);
}

int
main (void)
{
   unsigned char buffer[MAXLEN];
   struct sockaddr_in sin;
   struct hostent *host = gethostbyname(hostname);
   int len, l, rt;
   unsigned int channel;
   double tc;
   double tf;
   double hum;
   unsigned int address;
   unsigned int hs;
   unsigned int bs;

  //extern void init_sockaddr (struct sockaddr_in *name, const char *hostname, unsigned short int port);
  int sock;
  struct sockaddr_in servername;
   strcpy(lastWrite, "                                                 ");

  memset(AllSensors, 0, 3*12);

  /* Create the socket.   */
  sock = socket (PF_INET, SOCK_STREAM, 0);
  if (sock < 0)
    {
      perror ("socket (client)");
      exit (EXIT_FAILURE);
    }

   /*** PLACE DATA IN sockaddr_in struct ***/
   memcpy(&sin.sin_addr.s_addr, host->h_addr, host->h_length);
   sin.sin_family = AF_INET;
   sin.sin_port = htons(portno);

   /*** CONNECT SOCKET TO THE SERVICE DESCRIBED BY sockaddr_in struct ***/
   if (connect(sock, (struct sockaddr *)&sin, sizeof(sin)) < 0)
   {
      perror("connecting");
      exit (EXIT_FAILURE);
   }

  /* consume all old data */
  readPacket (sock, buffer);

  /* Send data to the server.   */
  write_to_server (sock,VariableLengthMode,2);
  await_input(sock, 500); /* wait UPTO 500ms */
  read_ack (sock);

  write_to_server (sock,EnableAllRF,2);
  await_input(sock, 500); /* wait UPTO 500ms */
  read_ack (sock);

  /* read values */
  while(1)
  {
    l= readPacket (sock, buffer);
    rt= validatePacket(l, buffer);
    if (!rt)
    {
//    printPacket(l, buffer);
      decodePacket(buffer,&channel,&tc,&tf,&hum,&address,&hs,&bs);
      logPacket(channel,tc,tf,hum,address,hs,bs);
      memcpy(&AllSensors[channel-1][0],buffer,11);

      /* print all sensors */
      WriteSensors(0);  // fahrenheit 
      WriteSensors(1);  // celsius
    }
  }
  close (sock);
  exit (EXIT_SUCCESS);
}

